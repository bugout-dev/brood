"""
Brood CLI
"""
import argparse
from distutils.util import strtobool
import json
from typing import List
import uuid

from . import actions
from . import data
from . import exceptions
from . import subscriptions
from .external import SessionLocal
from .models import (
    User,
    Group,
    Role,
    TokenType,
    Subscription,
    SubscriptionPlan,
    KVBrood,
    Application,
)


def print_user(user: User) -> None:
    """
    Print user to screen as JSON object.
    """
    print(json.dumps(actions.user_as_json_dict(user)))


def print_token(token: User) -> None:
    """
    Print token to screen as JSON object.
    """
    print(json.dumps(actions.token_as_json_dict(token)))


def print_verification_email(verification_email: User) -> None:
    """
    Print verification_email to screen as JSON object.
    """
    print(json.dumps(actions.verification_email_as_json_dict(verification_email)))


def print_group(group: Group) -> None:
    """
    Print group to screen as JSON object.
    """
    print(json.dumps(actions.group_as_json_dict(group)))


def print_group_users(group_users: data.GroupUserResponse) -> None:
    """
    Print group_users to screen as JSON object.
    """
    print(json.dumps(actions.group_users_as_json_dict(group_users)))


def users_create_handler(args: argparse.Namespace) -> None:
    """
    Handler for "users create" subcommand.
    """
    session = SessionLocal()
    try:
        user = actions.create_user(session, args.username, args.email, args.password)

        if args.verified:
            user.verified = True
            session.add(user)
            session.commit()

        print_user(user)
    finally:
        session.close()


def users_get_handler(args: argparse.Namespace) -> None:
    """
    Handler for "users get" subcommand.
    """
    session = SessionLocal()
    try:
        user = actions.get_user(session, username=args.username, email=args.email)
        print_user(user)
    finally:
        session.close()


def users_delete_handler(args: argparse.Namespace) -> None:
    """
    Handler for "users delete" subcommand.
    """
    session = SessionLocal()
    try:
        user = actions.delete_user(session, args.username, args.email)
        print_user(user)
    finally:
        session.close()


def users_newpassword_handler(args: argparse.Namespace) -> None:
    """
    Handler for "users newpassword" subcommand.
    """
    session = SessionLocal()
    try:
        user = actions.change_password(
            session,
            new_password=args.new_password,
            current_password=args.current_password,
            username=args.username,
            email=args.email,
        )
        print_user(user)
    finally:
        session.close()


def users_forcepassword_handler(args: argparse.Namespace) -> None:
    """
    Handler for "users forcepassword" subcommand.
    """
    session = SessionLocal()
    password_context = actions.get_password_context()
    try:
        new_password_hash = password_context.hash(args.new_password)
        user = actions.get_user(session, args.username, args.email)
        user.password_hash = new_password_hash
        session.add(user)
        session.commit()
        print_user(user)
    finally:
        session.close()


def limits_get_group_limit_handler(args: argparse.Namespace) -> None:
    """
    Handler for "users get_group_limit" subcommand.
    """
    session = SessionLocal()
    try:
        user = actions.get_user(session, args.username)
        group_limit = actions.get_user_group_limit(session, user.id)
        print(group_limit)
    finally:
        session.close()


def limits_set_group_limit_handler(args: argparse.Namespace) -> None:
    """
    Handler for "users set_group_limit" subcommand.
    """
    session = SessionLocal()
    try:
        user = actions.get_user(session, args.username)
        actions.set_user_group_limit(session, user.id, args.limit)
        print(args.limit)
    finally:
        session.close()


def verifications_send_handler(args: argparse.Namespace) -> None:
    """
    Handler for "users send" subcommand.
    """
    session = SessionLocal()
    try:
        verification_email = actions.send_verification_email(
            session, username=args.username, email=args.email
        )
        print_verification_email(verification_email)
    finally:
        session.close()


def verifications_complete_handler(args: argparse.Namespace) -> None:
    """
    Handler for "users complete" subcommand.
    """
    session = SessionLocal()
    try:
        user = actions.complete_verification(
            session, args.code, username=args.username, email=args.email
        )
        print_user(user)
    finally:
        session.close()


def tokens_create_handler(args: argparse.Namespace) -> None:
    """
    Handler for "tokens create" subcommand.
    """
    session = SessionLocal()
    try:
        user = actions.get_user(session, username=args.username, email=args.email)
        token = actions.create_token(
            session,
            user_id=user.id,
            token_type=TokenType.bugout,
            token_note="Bugout CLI token",
            restricted=args.restricted,
        )

        print_token(token)
    finally:
        session.close()


def tokens_get_handler(args: argparse.Namespace) -> None:
    """
    Handler for "tokens get" subcommand.
    """
    session = SessionLocal()
    try:
        token = actions.get_token(session, args.token)
        print_token(token)
    finally:
        session.close()


def tokens_revoke_handler(args: argparse.Namespace) -> None:
    """
    Handler for "tokens revoke" subcommand.
    """
    session = SessionLocal()
    try:
        if args.force:
            token_obj = actions.get_token(session, args.token)
            session.delete(token_obj)
            session.commit()
        else:
            token = actions.revoke_token(session, args.token)
            print_token(token)
    except:
        session.rollback()
    finally:
        session.close()


# Groups
def group_create_handler(args: argparse.Namespace) -> None:
    """
    Handler for "groups create" subcommand.
    """
    session = SessionLocal()
    try:
        user = actions.get_user(session, username=args.username)
        group = actions.create_group(session, args.name, user)
        print_group(group)
    finally:
        session.close()


def group_get_handler(args: argparse.Namespace) -> None:
    session = SessionLocal()
    try:
        if args.id is not None:
            groups_obj = actions.get_group(session, group_id=args.id)
        elif args.name is not None:
            groups_obj = actions.get_group(session, group_name=args.name)
        else:
            raise actions.GroupInvalidParameters(
                "In order to get group, at least one of group_id, or group_name must be specified"
            )
        groups = data.GroupListResponse(
            groups=[
                data.GroupResponse(
                    id=group.id,
                    name=group.name,
                    autogenerated=group.autogenerated,
                    subscriptions=[
                        subscription_plan.subscription_plan_id
                        for subscription_plan in group.subscriptions
                    ],
                    created_at=group.created_at,
                    updated_at=group.updated_at,
                )
                for group in groups_obj
            ]
        )
        print(groups.json())
    finally:
        session.close()


def group_list_handler(args: argparse.Namespace) -> None:
    session = SessionLocal()
    try:
        groups_obj = session.query(Group).all()
        groups = data.GroupListResponse(
            groups=[
                data.GroupResponse(
                    id=group.id,
                    name=group.name,
                    autogenerated=group.autogenerated,
                    subscriptions=[
                        subscription_plan.subscription_plan_id
                        for subscription_plan in group.subscriptions
                    ],
                    created_at=group.created_at,
                    updated_at=group.updated_at,
                )
                for group in groups_obj
            ]
        )
        print(groups.json())
    finally:
        session.close()


def group_role_handler(args: argparse.Namespace) -> None:
    """
    Handler for "groups role" subcommand.
    """
    session = SessionLocal()
    try:
        group = actions.get_group(session, group_id=args.group)
        group_users = actions.set_user_in_group(
            session,
            group_id=group.id,
            current_user_type=Role.owner,
            current_user_autogenerated=True,
            user_type=args.type,
            username=args.username,
        )
        print_group_users(group_users)
    finally:
        session.close()


def group_add_subscription_handler(args: argparse.Namespace) -> None:
    """
    Handler for "groups subscription add" subcommand.
    """
    session = SessionLocal()
    try:
        units = args.units
        applied_group_subscriptions = []
        plan = subscriptions.get_subscription_plan(session, args.plan)
        if plan.default_units is not None:
            units = plan.default_units

        for group_id in args.groups:
            group = session.query(Group).filter(Group.id == group_id).one_or_none()
            if group is None:
                continue
            group_subscription_ex = (
                session.query(Subscription)
                .filter(
                    Subscription.subscription_plan_id == plan.id,
                    Subscription.group_id == group.id,
                )
                .one_or_none()
            )
            if group_subscription_ex is not None:
                continue

            subscription_obj = subscriptions.add_group_subscription(
                session=session,
                group_id=group.id,
                plan_id=args.plan,
                units=units,
                active=bool(strtobool(args.active)),
                stripe_customer_id=args.stripe_customer_id,
                stripe_subscription_id=args.stripe_subscription_id,
            )
            subscription_obj_dict = actions.subscription_as_json_dict(subscription_obj)
            subscription_obj_dict["group_name"] = group.name
            applied_group_subscriptions.append(subscription_obj_dict)
        print(json.dumps(applied_group_subscriptions))
    finally:
        session.close()


def group_update_subscription_handler(args: argparse.Namespace) -> None:
    """
    Handler for "groups subscription update" subcommand.
    """
    session = SessionLocal()
    try:
        subscription_obj = subscriptions.update_group_subscription(
            session=session,
            group_id=args.group,
            plan_id=args.plan,
            stripe_customer_id=args.stripe_customer_id,
            stripe_subscription_id=args.stripe_subscription_id,
            units=args.units,
            active=bool(strtobool(args.active)) if args.active is not None else None,
        )
        print(json.dumps(actions.subscription_as_json_dict(subscription_obj)))
    finally:
        session.close()


def group_remove_subscription_handler(args: argparse.Namespace) -> None:
    """
    Handler for "groups subscription remove" subcommand.
    """
    session = SessionLocal()
    try:
        subscription_obj = subscriptions.remove_group_subscription(
            session, args.group, args.plan
        )
        print(json.dumps(actions.subscription_as_json_dict(subscription_obj)))
    finally:
        session.close()


# Subscription plans
def plan_create_handler(args: argparse.Namespace) -> None:
    """
    Creates new subscription plan.
    Controlled only by command line interface.
    """
    session = SessionLocal()
    try:
        plan_obj = SubscriptionPlan(
            name=args.name,
            description=args.description,
            stripe_product_id=args.stripe_product_id,
            stripe_price_id=args.stripe_price_id,
            default_units=args.default_units,
            plan_type=data.SubscriptionPlanType(args.plan_type).value,
            public=bool(strtobool(args.public)),
        )
        session.add(plan_obj)
        session.commit()

        if args.kv_key is not None:
            kv_brood = KVBrood(kv_key=args.kv_key, kv_value=plan_obj.id)
            session.add(kv_brood)
            session.commit()
        print(json.dumps(actions.plan_as_json_dict(plan_obj)))
    finally:
        session.close()


def plan_list_handler(args: argparse.Namespace) -> None:
    """
    Handler for "plans list" subcommand.
    """
    session = SessionLocal()
    try:
        plans_obj = subscriptions.get_subscription_plans(
            session,
        )
        plans = {
            "plans": [actions.plan_as_json_dict(plan_obj) for plan_obj in plans_obj]
        }
        print(json.dumps(plans))
    finally:
        session.close()


def plan_adopt_handler(args: argparse.Namespace) -> None:
    """
    Handler for "plans adopt" subcommand.

    This command associates the free subscription plan with all groups which do not currently have
    an associated subscription.
    """
    session = SessionLocal()
    try:
        free_plan_id = actions.get_kv_variable(
            session, "BUGOUT_GROUP_FREE_SUBSCRIPTION_PLAN"
        ).kv_value
        free_plan = subscriptions.get_subscription_plan(session, free_plan_id)

        group_ids_from_subscriptions_query = session.query(Subscription.group_id)
        orphan_group_ids_query = session.query(Group.id).filter(
            Group.id.notin_(group_ids_from_subscriptions_query)
        )
        orphan_group_ids = orphan_group_ids_query.all()
        groups_adopted = []
        for result in orphan_group_ids:
            group_id = result[0]
            session.add(
                Subscription(
                    group_id=group_id,
                    subscription_plan_id=free_plan.id,
                    seats=free_plan.default_units,
                    active=True,
                )
            )
            groups_adopted.append(str(group_id))
        session.commit()
    finally:
        session.close()

    for group_id in groups_adopted:
        print(group_id)


def plan_attr_update_handler(args: argparse.Namespace) -> None:
    """
    Handler for "plans attr update" subcommand.
    """
    session = SessionLocal()
    try:
        subscriptions.get_subscription_plan(session, args.id)

        plan_obj = subscriptions.update_subscription_plan(
            session,
            id=args.id,
            name=args.name,
            description=args.description,
            stripe_product_id=args.stripe_product_id,
            stripe_price_id=args.stripe_price_id,
            default_units=args.default_units,
            plan_type=args.plan_type,
        )
        print(json.dumps(actions.plan_as_json_dict(plan_obj)))
    finally:
        session.close()


def plan_attr_remove_handler(args: argparse.Namespace) -> None:
    """
    Removes Subscription Plan attribute value and set it as None
    if database Model allow it. Should be provided name of attribute.
    """
    session = SessionLocal()
    try:
        query = session.query(SubscriptionPlan).filter(SubscriptionPlan.id == args.id)
        query.update({getattr(SubscriptionPlan, args.attr): None})
        session.commit()

        plan_obj = query.first()
        print(json.dumps(actions.plan_as_json_dict(plan_obj)))
    finally:
        session.close()


def plan_remove_handler(args: argparse.Namespace) -> None:
    """
    Removes Bugout Subscription Plan by id.
    """
    session = SessionLocal()
    try:
        plan_obj = (
            session.query(SubscriptionPlan)
            .filter(SubscriptionPlan.id == args.id)
            .one_or_none()
        )
        if plan_obj is None:
            raise subscriptions.SubscriptionPlanNotFound(
                f"There is no Subscription Plan with id: {args.id}."
            )
        session.delete(plan_obj)
        session.commit()

        print(json.dumps(actions.plan_as_json_dict(plan_obj)))
    finally:
        session.close()


def kv_list_handler(args: argparse.Namespace) -> None:
    """
    Handler for "kv list" subcommand.
    """
    session = SessionLocal()
    try:
        kv_brood_list = session.query(KVBrood).all()
        print(
            json.dumps(
                {
                    "kv_variables": [
                        actions.kv_brood_as_json_dict(kv_brood)
                        for kv_brood in kv_brood_list
                    ]
                }
            )
        )
    finally:
        session.close()


def kv_create_handler(args: argparse.Namespace) -> None:
    """
    Handler for "kv create" subcommand.
    """
    session = SessionLocal()
    try:
        kv_brood = KVBrood(kv_key=args.kv_key, kv_value=args.kv_value)
        session.add(kv_brood)
        session.commit()

        print(json.dumps(actions.kv_brood_as_json_dict(kv_brood)))
    finally:
        session.close()


def kv_get_handler(args: argparse.Namespace) -> None:
    """
    Handler for "kv get" subcommand.
    """
    session = SessionLocal()
    try:
        kv_brood = actions.get_kv_variable(session, args.kv_key)

        print(json.dumps(actions.kv_brood_as_json_dict(kv_brood)))
    finally:
        session.close()


def kv_delete_handler(args: argparse.Namespace) -> None:
    """
    Handler for "kv delete" subcommand.
    """
    session = SessionLocal()
    try:
        kv_brood = (
            session.query(KVBrood).filter(KVBrood.kv_key == args.kv_key).one_or_none()
        )
        if kv_brood is None:
            raise actions.KVBroodNotFound("Variable not found in KVBrood table")
        session.delete(kv_brood)
        session.commit()

        print(json.dumps(actions.kv_brood_as_json_dict(kv_brood)))
    finally:
        session.close()


def applications_list_handler(args: argparse.Namespace) -> None:
    """
    Handler for "applications list" command.
    """
    session = SessionLocal()
    try:
        query = session.query(Application)
        if args.group is not None:
            query = query.filter(Application.group_id == args.group)

        applications = query.all()

        print(
            json.dumps(
                {
                    "applications": [
                        actions.application_as_json_dict(application)
                        for application in applications
                    ]
                }
            )
        )
    finally:
        session.close()


def application_create_handler(args: argparse.Namespace) -> None:
    session = SessionLocal()
    try:
        application = Application(
            group_id=args.group,
            name=args.name,
            description=args.description,
        )
        session.add(application)
        session.commit()
        print(json.dumps(actions.application_as_json_dict(application)))
    finally:
        session.close()


def application_migrate_handler(args: argparse.Namespace) -> None:
    session = SessionLocal()
    try:
        query = session.query(Application).filter(Application.id == args.application)
        application = query.one_or_none()
        if application is None:
            raise exceptions.ApplicationsNotFound("Application not found")

        query.update({Application.group_id: args.group})
        session.commit()
        print(json.dumps(actions.application_as_json_dict(application)))
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Brood CLI")
    parser.set_defaults(func=lambda _: parser.print_help())
    subcommands = parser.add_subparsers(description="Brood commands")

    parser_users = subcommands.add_parser("users", description="Brood users")
    parser_users.set_defaults(func=lambda _: parser_users.print_help())
    subcommands_users = parser_users.add_subparsers(description="Brood user commands")

    # User command parser
    parser_users_create = subcommands_users.add_parser(
        "create", description="Create Brood user"
    )
    parser_users_create.add_argument(
        "-u",
        "--username",
        required=True,
        help="Username of the user to create",
    )
    parser_users_create.add_argument(
        "-e",
        "--email",
        required=True,
        help="Email of the user to create",
    )
    parser_users_create.add_argument(
        "-p",
        "--password",
        required=True,
        help="Password of the user to create",
    )
    parser_users_create.add_argument(
        "--verified",
        action="store_true",
        help="Set this flag to create a verified user",
    )
    parser_users_create.set_defaults(func=users_create_handler)

    parser_users_get = subcommands_users.add_parser("get", description="Get Brood user")
    parser_users_get.add_argument(
        "-u",
        "--username",
        help="Username of the user to get",
    )
    parser_users_get.add_argument(
        "-e",
        "--email",
        help="Email of the user to get",
    )
    parser_users_get.set_defaults(func=users_get_handler)

    parser_users_delete = subcommands_users.add_parser(
        "delete", description="Delete Brood user"
    )
    parser_users_delete.add_argument(
        "-u",
        "--username",
        help="Username of the user to delete",
    )
    parser_users_delete.add_argument(
        "-e",
        "--email",
        help="Email of the user to delete",
    )
    parser_users_delete.set_defaults(func=users_delete_handler)

    parser_users_newpassword = subcommands_users.add_parser(
        "newpassword", description="Update password"
    )
    parser_users_newpassword.add_argument(
        "-u",
        "--username",
        help="Username of the user to update password for",
    )
    parser_users_newpassword.add_argument(
        "-e",
        "--email",
        help="Email of the user to update password for",
    )
    parser_users_newpassword.add_argument(
        "-p",
        "--current-password",
        help="Current password for user",
    )
    parser_users_newpassword.add_argument("new_password", help="New password")
    parser_users_newpassword.set_defaults(func=users_newpassword_handler)

    parser_users_forcepassword = subcommands_users.add_parser(
        "forcepassword", description="Update password"
    )
    parser_users_forcepassword.add_argument(
        "-u",
        "--username",
        help="Username of the user to update password for",
    )
    parser_users_forcepassword.add_argument(
        "-e",
        "--email",
        help="Email of the user to update password for",
    )
    parser_users_forcepassword.add_argument("new_password", help="New password")
    parser_users_forcepassword.set_defaults(func=users_forcepassword_handler)

    parser_limits = subcommands.add_parser("limits", description="Brood limits")
    parser_limits.set_defaults(func=lambda _: parser_limits.print_help())
    subcommands_limits = parser_limits.add_subparsers(
        description="Brood limits commands"
    )
    parser_users_get_group_limit = subcommands_limits.add_parser(
        "get_group_limit", description="Get group limit for user"
    )
    parser_users_get_group_limit.add_argument("-u", "--username", help="Username")
    parser_users_get_group_limit.set_defaults(func=limits_get_group_limit_handler)

    parser_users_set_group_limit = subcommands_limits.add_parser(
        "set_group_limit", description="Set group limit for user"
    )
    parser_users_set_group_limit.add_argument("-u", "--username", help="Username")
    parser_users_set_group_limit.add_argument(
        "-l", "--limit", type=int, help="Group limit to assign to user"
    )
    parser_users_set_group_limit.set_defaults(func=limits_set_group_limit_handler)

    # Verification email command parser
    parser_verifications = subcommands.add_parser(
        "verifications", description="Brood user verifications"
    )
    parser_verifications.set_defaults(func=lambda _: parser_verifications.print_help())
    subcommands_verifications = parser_verifications.add_subparsers(
        description="Brood user verification commands"
    )

    parser_verifications_send = subcommands_verifications.add_parser(
        "send", description="Send Brood user verification email"
    )
    parser_verifications_send.add_argument(
        "-u",
        "--username",
        help="Username of the user to verify",
    )
    parser_verifications_send.add_argument(
        "-e",
        "--email",
        help="Email of the user to verify",
    )
    parser_verifications_send.set_defaults(func=verifications_send_handler)

    parser_verifications_complete = subcommands_verifications.add_parser(
        "complete", description="Complete Brood user verification"
    )
    parser_verifications_complete.add_argument(
        "-u",
        "--username",
        help="Username of the user to complete verification for",
    )
    parser_verifications_complete.add_argument(
        "-e",
        "--email",
        help="Email of the user to complete verification for",
    )
    parser_verifications_complete.add_argument(
        "code",
        help="Verification code to complete verification with",
    )
    parser_verifications_complete.set_defaults(func=verifications_complete_handler)

    # Tokens command parser
    parser_tokens = subcommands.add_parser("tokens", description="Brood tokens")
    parser_tokens.set_defaults(func=lambda _: parser_tokens.print_help())
    subcommands_tokens = parser_tokens.add_subparsers(
        description="Brood token commands"
    )
    parser_tokens_create = subcommands_tokens.add_parser(
        "create", description="Generate token for Brood user"
    )
    parser_tokens_create.add_argument(
        "-u",
        "--username",
        help="Username of the user to complete verification for",
    )
    parser_tokens_create.add_argument(
        "-e",
        "--email",
        help="Email of the user to complete verification for",
    )
    parser_tokens_create.add_argument(
        "-R",
        "--restricted",
        action="store_true",
        help="Set this flag to generate a restricted token for this user",
    )
    parser_tokens_create.set_defaults(func=tokens_create_handler)

    parser_tokens_get = subcommands_tokens.add_parser(
        "get", description="Get specified token"
    )
    parser_tokens_get.add_argument(
        "token", type=uuid.UUID, help="Token to retrieve from database"
    )
    parser_tokens_get.set_defaults(func=tokens_get_handler)

    parser_tokens_revoke = subcommands_tokens.add_parser(
        "revoke", description="Revoke specified token"
    )
    parser_tokens_revoke.add_argument(
        "token", type=uuid.UUID, help="Token to retrieve from database"
    )
    parser_tokens_revoke.add_argument(
        "--force",
        action="store_true",
        help="Set this flag to revoke the token no matter what",
    )
    parser_tokens_revoke.set_defaults(func=tokens_revoke_handler)

    # Groups command parser
    parser_groups = subcommands.add_parser("groups", description="Brood groups")
    parser_groups.set_defaults(func=lambda _: parser_groups.print_help())
    subcommands_groups = parser_groups.add_subparsers(
        description="Brood group commands"
    )
    parser_groups_create = subcommands_groups.add_parser(
        "create", description="Create Brood group"
    )
    parser_groups_create.add_argument(
        "-n",
        "--name",
        required=True,
        help="Group name",
    )
    parser_groups_create.add_argument(
        "-u",
        "--username",
        required=True,
        help="Username of the group owner",
    )
    parser_groups_create.set_defaults(func=group_create_handler)

    parser_groups_get = subcommands_groups.add_parser(
        "get", description="Get Brood group"
    )
    parser_groups_get.add_argument(
        "-n",
        "--name",
        help="Group name",
    )
    parser_groups_get.add_argument(
        "-i",
        "--id",
        help="Group id",
    )
    parser_groups_get.set_defaults(func=group_get_handler)

    parser_groups_list = subcommands_groups.add_parser(
        "list", description="List all Brood group"
    )
    parser_groups_list.set_defaults(func=group_list_handler)

    parser_groups_role = subcommands_groups.add_parser(
        "role", description="Add user to Brood group and set role"
    )
    parser_groups_role.add_argument(
        "-g",
        "--group",
        type=uuid.UUID,
        required=True,
        help="Group id",
    )
    parser_groups_role.add_argument(
        "-u",
        "--username",
        required=True,
        help="Added user username",
    )
    parser_groups_role.add_argument(
        "-t",
        "--type",
        required=True,
        help=f"User type: {[member for member in Role.__members__]}",
    )
    parser_groups_role.set_defaults(func=group_role_handler)

    parser_groups_subscription = subcommands_groups.add_parser(
        "subscription", description="Brood group subscription"
    )
    parser_groups_subscription.set_defaults(
        func=lambda _: parser_groups_subscription.print_help()
    )
    subcommands_groups_subscription = parser_groups_subscription.add_subparsers(
        description="Brood group subscription commands"
    )
    parser_groups_subscription_add = subcommands_groups_subscription.add_parser(
        "add", description="Add subscription plan to group"
    )
    parser_groups_subscription_add.add_argument(
        "-g",
        "--groups",
        nargs="+",
        type=uuid.UUID,
        required=True,
        help="Groups ids",
    )
    parser_groups_subscription_add.add_argument(
        "-p",
        "--plan",
        type=uuid.UUID,
        required=True,
        help="Subscription plan Bugout ID",
    )
    parser_groups_subscription_add.add_argument(
        "--stripe_customer_id",
        help="Stripe customer ID",
    )
    parser_groups_subscription_add.add_argument(
        "--stripe_subscription_id",
        help="Stripe subscription ID",
    )
    parser_groups_subscription_add.add_argument(
        "-u",
        "--units",
        help="Set units for group subscription, it will use default_units if specified for plan",
    )
    parser_groups_subscription_add.add_argument(
        "-a",
        "--active",
        choices=["True", "False"],
        help="Active status of Subscription",
    )
    parser_groups_subscription_add.set_defaults(func=group_add_subscription_handler)

    parser_groups_subscription_update = subcommands_groups_subscription.add_parser(
        "update", description="Update subscription plan for group"
    )
    parser_groups_subscription_update.add_argument(
        "-g",
        "--group",
        type=uuid.UUID,
        help="Group id",
    )
    parser_groups_subscription_update.add_argument(
        "-p",
        "--plan",
        type=uuid.UUID,
        help="Subscription plan Bugout ID",
    )
    parser_groups_subscription_update.add_argument(
        "--stripe_customer_id",
        help="Stripe customer ID",
    )
    parser_groups_subscription_update.add_argument(
        "--stripe_subscription_id",
        help="Stripe subscription ID",
    )
    parser_groups_subscription_update.add_argument(
        "-u",
        "--units",
        help="Set units for group subscription",
    )
    parser_groups_subscription_update.add_argument(
        "-a",
        "--active",
        choices=["True", "False"],
        help="Active status of Subscription",
    )
    parser_groups_subscription_update.set_defaults(
        func=group_update_subscription_handler
    )

    parser_groups_subscription_remove = subcommands_groups_subscription.add_parser(
        "remove", description="Remove subscription plan from group"
    )
    parser_groups_subscription_remove.add_argument(
        "-g",
        "--group",
        type=uuid.UUID,
        required=True,
        help="Group ID",
    )
    parser_groups_subscription_remove.add_argument(
        "-p",
        "--plan",
        type=uuid.UUID,
        required=True,
        help="Subscription plan Bugout ID",
    )
    parser_groups_subscription_remove.set_defaults(
        func=group_remove_subscription_handler
    )

    # Subscription plans command parser
    parser_plans = subcommands.add_parser(
        "plans", description="Brood subscription plans"
    )
    parser_plans.set_defaults(func=lambda _: parser_plans.print_help())
    subcommands_plans = parser_plans.add_subparsers(
        description="Brood subscription plans commands"
    )
    parser_plans_create = subcommands_plans.add_parser(
        "create", description="Create new subscription plan"
    )
    parser_plans_create.add_argument(
        "-n", "--name", required=True, help="Name of subscription plan"
    )
    parser_plans_create.add_argument(
        "-d", "--description", help="Description of subscription plan"
    )
    parser_plans_create.add_argument(
        "--stripe_product_id", help="Srtipe product ID if exists"
    )
    parser_plans_create.add_argument(
        "--stripe_price_id", help="Srtipe price ID if exists"
    )
    parser_plans_create.add_argument(
        "--kv_key",
        help="If kv_key name provided it will create a row in"
        "KVBrood table with kv_key name and kv_value as subscription plan id",
    )
    parser_plans_create.add_argument("--default_units", help="Default units for plan")
    parser_plans_create.add_argument(
        "--plan_type",
        required=True,
        help=f"Plan type: {[member for member in data.SubscriptionPlanType.__members__]}",
    )
    parser_plans_create.add_argument(
        "-p",
        "--public",
        choices=["True", "False"],
        help="Public or not Subscription Plan",
    )
    parser_plans_create.set_defaults(func=plan_create_handler)

    parser_plans_list = subcommands_plans.add_parser(
        "list", description="Get list of subscription plans"
    )
    parser_plans_list.set_defaults(func=plan_list_handler)

    parser_plans_attr = subcommands_plans.add_parser(
        "attr", description="Brood subscription plan attributes"
    )
    parser_plans_attr.set_defaults(func=lambda _: parser_plans_attr.print_help())
    subcommands_plans_attr = parser_plans_attr.add_subparsers(
        description="Brood subscription plan attribute commands"
    )
    subcommands_plans_attr_update = subcommands_plans_attr.add_parser(
        "update", description="Update subscription plan attribute"
    )
    subcommands_plans_attr_update.add_argument(
        "-i", "--id", type=uuid.UUID, required=True, help="Subscription plan Bugout ID"
    )
    subcommands_plans_attr_update.add_argument(
        "-n", "--name", help="Name of subscription plan"
    )
    subcommands_plans_attr_update.add_argument(
        "-d", "--description", help="Description of subscription plan plan"
    )
    subcommands_plans_attr_update.add_argument(
        "--stripe_product_id", help="Srtipe product ID if exists"
    )
    subcommands_plans_attr_update.add_argument(
        "--stripe_price_id", help="Srtipe price ID if exists"
    )
    subcommands_plans_attr_update.add_argument(
        "--default_units", help="Default units for plan"
    )
    subcommands_plans_attr_update.add_argument(
        "--plan_type",
        help=f"Plan type: {[member for member in data.SubscriptionPlanType.__members__]}",
    )
    subcommands_plans_attr_update.set_defaults(func=plan_attr_update_handler)
    parser_plans_attr_remove = subcommands_plans_attr.add_parser(
        "remove", description="Clear Subscription Plan attribute"
    )
    parser_plans_attr_remove.add_argument(
        "-i",
        "--id",
        type=uuid.UUID,
        required=True,
        help="Subscription plan Bugout ID",
    )
    parser_plans_attr_remove.add_argument(
        "-a",
        "--attr",
        required=True,
        help="Attribute to clear",
    )
    parser_plans_attr_remove.set_defaults(func=plan_attr_remove_handler)

    parser_plans_remove = subcommands_plans.add_parser(
        "remove", description="Remove subscription plan"
    )
    parser_plans_remove.add_argument(
        "-i", "--id", required=True, help="Subscription plan Bugout ID"
    )
    parser_plans_remove.set_defaults(func=plan_remove_handler)

    parser_plans_adopt = subcommands_plans.add_parser(
        "adopt",
        description=(
            "Subscribe every unsubscribed group to the free plan (specified by the "
            "BUGOUT_GROUPS_FREE_SUBSCRIPTION_PLAN environment variable)"
        ),
    )
    parser_plans_adopt.set_defaults(func=plan_adopt_handler)

    # KV command parser
    parser_kv = subcommands.add_parser("kv", description="Brood kv variables")
    parser_kv.set_defaults(func=lambda _: parser_kv.print_help())
    subcommands_kv = parser_kv.add_subparsers(description="Brood kv variables commands")
    parser_kv_list = subcommands_kv.add_parser(
        "list", description="List all kv brood variables"
    )
    parser_kv_list.set_defaults(func=kv_list_handler)
    parser_kv_create = subcommands_kv.add_parser(
        "create", description="Create new kv brood variable"
    )
    parser_kv_create.add_argument(
        "-k", "--kv_key", required=True, help="Name of variable"
    )
    parser_kv_create.add_argument(
        "-v", "--kv_value", required=True, help="Variable value"
    )
    parser_kv_create.set_defaults(func=kv_create_handler)
    parser_kv_get = subcommands_kv.add_parser(
        "get", description="Get kv brood variable"
    )
    parser_kv_get.add_argument("-k", "--kv_key", required=True, help="Name of variable")
    parser_kv_get.set_defaults(func=kv_get_handler)
    parser_kv_delete = subcommands_kv.add_parser(
        "delete", description="Delete kv brood variable"
    )
    parser_kv_delete.add_argument(
        "-k", "--kv_key", required=True, help="Name of variable"
    )
    parser_kv_delete.set_defaults(func=kv_delete_handler)

    # Applications command parser
    parser_applications = subcommands.add_parser(
        "applications", description="Brood applications"
    )
    parser_applications.set_defaults(func=lambda _: parser_applications.print_help())
    subcommands_applications = parser_applications.add_subparsers(
        description="Brood application commands"
    )
    parser_applications_list = subcommands_applications.add_parser(
        "list", description="List all applications"
    )
    parser_applications_list.add_argument(
        "-g", "--group", help="Filter applications by group ID"
    )
    parser_applications_list.set_defaults(func=applications_list_handler)
    parser_applications_create = subcommands_applications.add_parser(
        "create", description="Create new application"
    )
    parser_applications_create.add_argument(
        "-g", "--group", required=True, help="Filter applications by group ID"
    )
    parser_applications_create.add_argument(
        "-n", "--name", required=True, help="Name of application"
    )
    parser_applications_create.add_argument(
        "-d", "--description", help="Description of application"
    )
    parser_applications_create.set_defaults(func=application_create_handler)
    parser_applications_migrate = subcommands_applications.add_parser(
        "migrate", description="Migrate application to another group"
    )
    parser_applications_migrate.add_argument(
        "-a", "--application", required=True, help="Applications ID"
    )
    parser_applications_migrate.add_argument(
        "-g", "--group", required=True, help="Group ID migrate to"
    )
    parser_applications_migrate.set_defaults(func=application_migrate_handler)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
