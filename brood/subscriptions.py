import logging
from typing import Any, List, Optional
from uuid import UUID

import stripe  # type: ignore
from sqlalchemy.orm.session import Session

from .data import (
    SubscriptionSessionType,
    SubscriptionPlanType,
    SubscriptionManageResponse,
)
from .models import Group, Subscription, SubscriptionPlan, KVBrood
from .settings import BUGOUT_URL

logger = logging.getLogger(__name__)


class SubscriptionInvalidParameters(ValueError):
    """
    Raised when operations are applied to a group subscription but invalid parameters are provided.
    """


class SubscriptionPlanInvalidParameters(ValueError):
    """
    Raised when operations are applied to a subscription plan but invalid parameters
    are provided with which to specify that plan.
    """


class SubscriptionPlanNotFound(Exception):
    """
    Raised when subscription plan with the given parameters is not found in the database.
    """


class GroupSubscriptionNotFound(Exception):
    """
    Raised when group subscription with the given parameters is not found in the database.
    """


class GroupSubscriptionAlreadyExists(Exception):
    """
    Raised when group subscription already attached to group.
    """


# Subscription plans


def get_subscription_plan(
    session: Session, subscription_plan_id: UUID
) -> SubscriptionPlan:
    """
    Get Bugout Subscription Plan by provided subscription_plan_id.
    """
    subscription_plan = (
        session.query(SubscriptionPlan)
        .filter(SubscriptionPlan.id == subscription_plan_id)
        .one_or_none()
    )
    if subscription_plan is None:
        raise SubscriptionPlanNotFound(
            f"Did not find subscription plan with id={subscription_plan_id}"
        )
    return subscription_plan


def get_subscription_plans(
    db_session: Session,
    plan_type: Optional[SubscriptionPlanType] = None,
    public_or_not: Optional[bool] = None,
) -> List[SubscriptionPlan]:
    """
    Extract list of subscription plans according to parameters.
    """
    query = db_session.query(SubscriptionPlan)
    if plan_type is not None:
        query = query.filter(SubscriptionPlan.plan_type == plan_type.value)
    if public_or_not is not None:
        query = query.filter(SubscriptionPlan.public == public_or_not)

    subscription_plans = query.all()
    if len(subscription_plans) < 0:
        raise SubscriptionPlanNotFound(f"Did not find any subscription plan")

    return subscription_plans


def update_subscription_plan(
    session: Session, id: UUID, **kwargs: Optional[Any]
) -> SubscriptionPlan:
    """
    Updates Subscription Plan if new values provided.
    """
    query = session.query(SubscriptionPlan).filter(SubscriptionPlan.id == id)
    for attr, value in kwargs.items():
        if value is not None:
            query.update({getattr(SubscriptionPlan, attr): value})
    session.commit()

    subscription_plan = query.first()
    return subscription_plan


def get_subscription_plan_by_units(
    db_session: Session, plan_type: SubscriptionPlanType, units_required: int
) -> SubscriptionPlan:
    """
    Return FREE plan if negative units provided.
    """
    plan_paid_type = "PRO"
    if units_required < 0:
        plan_paid_type = "FREE"

    if plan_type == SubscriptionPlanType.seats:
        kv_key = f"BUGOUT_GROUP_{plan_paid_type}_SUBSCRIPTION_PLAN"
    elif plan_type == SubscriptionPlanType.events:
        kv_key = f"BUGOUT_HUMBUG_MONTHLY_EVENTS_{plan_paid_type}_SUBSCRIPTION_PLAN"
    else:
        logger.error(f"Unsupported plan_type: {plan_type}")
        raise SubscriptionPlanNotFound("Did not find subscription plan")

    kv_variable = (
        db_session.query(KVBrood).filter(KVBrood.kv_key == kv_key).one_or_none()
    )
    if kv_variable is None:
        raise SubscriptionPlanNotFound(
            "Did not find KVBrood variable for subscription plan"
        )

    plan = (
        db_session.query(SubscriptionPlan)
        .filter(
            SubscriptionPlan.plan_type == plan_type.value,
            SubscriptionPlan.id == kv_variable.kv_value,
        )
        .one_or_none()
    )
    if plan is None:
        logger.error(
            f"Subscription plan not found, but should exist for kv_key: {kv_key}"
        )
        raise SubscriptionPlanNotFound("Did not find subscription plan")

    return plan


def get_subscription_plan_by_stripe_data(
    db_session: Session, stripe_product_id: str, stripe_price_id: str
) -> SubscriptionPlan:
    query = db_session.query(SubscriptionPlan).filter(
        SubscriptionPlan.stripe_product_id == stripe_product_id,
        SubscriptionPlan.stripe_price_id == stripe_price_id,
    )
    plan = query.one_or_none()
    if plan is None:
        raise SubscriptionPlanNotFound("Did not find subscription plan")

    return plan


# Group subscriptions


def get_group_subscription(
    session: Session,
    group_id: Optional[UUID] = None,
    plan_id: Optional[UUID] = None,
    stripe_customer_id: Optional[str] = None,
) -> Optional[Subscription]:
    """
    Get group subscription if it exists or return None.
    """
    query = session.query(Subscription)

    if group_id is not None and plan_id is not None:
        query = query.filter(
            Subscription.group_id == group_id,
            Subscription.subscription_plan_id == plan_id,
        )
    elif stripe_customer_id is not None:
        query = query.filter(Subscription.stripe_customer_id == stripe_customer_id)
    else:
        raise SubscriptionInvalidParameters(
            "In order to get group subscription, at least one of group_id "
            "with plan_id or stripe_customer_id must be specified."
        )

    subscription = query.one_or_none()
    return subscription


def get_group_subscriptions(
    session: Session, group_id: UUID, active: Optional[bool] = None
) -> List[Subscription]:
    """
    Get group subscriptions.
    """
    query = session.query(Subscription).filter(Subscription.group_id == group_id)
    if active is not None:
        query = query.filter(Subscription.active == active)
    group_subscriptions = query.all()
    return group_subscriptions


def add_group_subscription(
    session: Session,
    group_id: UUID,
    plan_id: UUID,
    units: int,
    active: bool,
    stripe_customer_id: Optional[str] = None,
    stripe_subscription_id: Optional[str] = None,
) -> Subscription:
    """
    Add group subscription plan.
    """
    subscription = Subscription(
        group_id=group_id,
        subscription_plan_id=plan_id,
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=stripe_subscription_id,
        units=units,
        active=active,
    )

    session.add(subscription)
    session.commit()

    return subscription


def add_volume_subscription(
    db_session: Session,
    plan: SubscriptionPlan,
    group: Group,
    units_required: int,
) -> SubscriptionManageResponse:
    """
    Generated Stripe customer or extract existen and create group subscription.
    """
    subscription = get_group_subscription(db_session, group.id, plan.id)

    # Generate new Stripe user with unpaid group subscription or retrieve existing customer.
    if subscription is None:
        customer = stripe.Customer.create(
            description=group.name,
        )
        subscription = add_group_subscription(
            session=db_session,
            group_id=group.id,
            plan_id=plan.id,
            units=0,
            active=False,
            stripe_customer_id=customer.id,
        )
    else:
        customer = stripe.Customer.retrieve(subscription.stripe_customer_id)

    session_type = SubscriptionSessionType.none
    session_id = None
    session_url = None

    if subscription.stripe_subscription_id is None:
        # Handle first subscription
        st_session = stripe_checkout(customer.id, plan, units_required)
        session_type = SubscriptionSessionType.checkout
        session_id = st_session.id
        logger.info(f"Created checkout session for customer with id: {customer.id}")
    else:
        st_session = stripe_customer_portal(subscription.stripe_customer_id)
        session_type = SubscriptionSessionType.portal
        session_url = st_session.url
        logger.info(
            f"Customer with id: {subscription.stripe_customer_id} redirected to customer portal"
        )

    return SubscriptionManageResponse(
        plan_id=plan.id,
        session_type=session_type,
        session_url=session_url,
        session_id=session_id,
    )


def add_internal_subscription(
    db_session: Session,
    plan: SubscriptionPlan,
    group: Group,
    units_required: int,
) -> SubscriptionManageResponse:
    """
    Add Free or internal subscriptions to group.
    """
    add_group_subscription(
        session=db_session,
        group_id=group.id,
        plan_id=plan.id,
        units=units_required,
        active=True,
    )
    session_type = SubscriptionSessionType.humbug
    session_id = None
    session_url = None

    return SubscriptionManageResponse(
        plan_id=plan.id,
        session_type=session_type,
        session_url=session_url,
        session_id=session_id,
    )


def update_group_subscription(
    session: Session,
    group_id: UUID,
    plan_id: UUID,
    **kwargs: Optional[Any],
) -> Subscription:
    """
    Updates group subscription attributes by provided group_id and plan_id.
    """
    if plan_id is None and group_id is None:
        raise SubscriptionInvalidParameters(
            "In order to update group subscription, plan_id with group_id must be specified."
        )
    query = (
        session.query(Subscription)
        .with_for_update()
        .filter(
            Subscription.subscription_plan_id == plan_id,
            Subscription.group_id == group_id,
        )
    )
    subscription = query.one_or_none()
    if subscription is None:
        raise GroupSubscriptionNotFound("Subscription for group not found.")

    for attr, value in kwargs.items():
        if value is not None:
            query.update({getattr(Subscription, attr): value})
    session.commit()

    subscription = query.first()
    return subscription


def update_group_subscription_by_customer(
    session: Session,
    group_id: UUID,
    plan_id: UUID,
    stripe_customer_id: str,
    **kwargs: Optional[Any],
) -> Subscription:
    """
    Updates group subscription attributes by stripe_customer_id.
    """
    query = (
        session.query(Subscription)
        .with_for_update()
        .filter(
            Subscription.group_id == group_id,
            Subscription.subscription_plan_id == plan_id,
            Subscription.stripe_customer_id == stripe_customer_id,
        )
    )
    subscription = query.one_or_none()
    if subscription is None:
        raise GroupSubscriptionNotFound("Subscription for group not found.")
    for attr, value in kwargs.items():
        if value is not None:
            query.update({getattr(Subscription, attr): value})
    session.commit()

    subscription = query.first()
    return subscription


def remove_group_subscription(
    session: Session, group_id: UUID, plan_id: UUID
) -> Subscription:
    """
    Removes group subscription.
    """
    subscription = (
        session.query(Subscription)
        .with_for_update()
        .filter(
            Subscription.group_id == group_id,
            Subscription.subscription_plan_id == plan_id,
        )
        .one_or_none()
    )
    if subscription is None:
        raise GroupSubscriptionNotFound(
            f"Did not find group subscription with group id: {group_id} and plan id: {plan_id}"
        )
    session.delete(subscription)
    session.commit()

    return subscription


def stripe_customer_portal(stripe_customer_id: str) -> stripe.billing_portal.Session:
    """
    Generates portal session where user will be redirected and be able
    to manage customer, payment and subscription details.

    Docs: https://stripe.com/docs/billing/subscriptions/integrating-customer-portal#redirect
    """
    st_session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=BUGOUT_URL,
    )
    return st_session


def stripe_checkout(
    stripe_customer_id: str, plan: SubscriptionPlan, units_required: int
) -> stripe.checkout.Session:
    """
    Handles new subscription creation for provided stripe_customer_id according
    with Bugout Subscription Plan data.
    Param seats_required is final quantity of allowed user seats for group subscription.

    Docs: https://stripe.com/docs/api/checkout/sessions
    """
    base_url = BUGOUT_URL
    if len(base_url) > 0 and base_url[-1] == "/":
        base_url = base_url[:-1]
    redirect_url = f"{base_url}/account/teams"
    st_session = stripe.checkout.Session.create(
        customer=stripe_customer_id,
        success_url=redirect_url,
        cancel_url=redirect_url,
        payment_method_types=["card"],
        mode="subscription",
        line_items=[
            {
                "price": plan.stripe_price_id,
                "description": plan.description,
                "quantity": units_required,
            }
        ],
    )
    return st_session
