"""
Brood resources CLI
"""
import argparse
import json

from .models import Resource
from ..external import SessionLocal


def resources_list_handler(args: argparse.Namespace) -> None:
    session = SessionLocal()
    try:
        query = session.query(Resource)
        if args.application is not None:
            query = query.filter(Resource.application_id == args.application)
        resources = query.all()

        print(
            json.dumps(
                {
                    "resources": [
                        {
                            "id": str(resource.id),
                            "application_id": str(resource.application_id),
                            "resource_data": resource.resource_data,
                            "created_at": str(resource.created_at),
                            "updated_at": str(resource.updated_at),
                        }
                        for resource in resources
                    ]
                }
            )
        )
    finally:
        session.close()


def resources_create_handler(args: argparse.Namespace) -> None:
    session = SessionLocal()
    try:
        resource = Resource(
            application_id=args.application,
            resource_data=json.loads(args.data),
        )
        session.add(resource)
        session.commit()

        print(
            json.dumps(
                {
                    "id": str(resource.id),
                    "application_id": str(resource.application_id),
                    "resource_data": resource.resource_data,
                    "created_at": str(resource.created_at),
                    "updated_at": str(resource.updated_at),
                }
            )
        )
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Brood resources CLI")
    parser.set_defaults(func=lambda _: parser.print_help())
    subcommands = parser.add_subparsers(description="Brood resources commands")

    parser_resources = subcommands.add_parser(
        "resources", description="Brood resources"
    )
    parser_resources.set_defaults(func=lambda _: parser_resources.print_help())
    subcommands_resources = parser_resources.add_subparsers(
        description="Brood user commands"
    )

    # Resources command parser
    parser_resources_list = subcommands_resources.add_parser(
        "list", description="List Brood resources"
    )
    parser_resources_list.add_argument(
        "-a",
        "--application",
        help="Application ID filter",
    )
    parser_resources_list.set_defaults(func=resources_list_handler)
    parser_resources_create = subcommands_resources.add_parser(
        "create", description="Create Brood resources"
    )
    parser_resources_create.add_argument(
        "-a",
        "--application",
        help="Application ID filter",
    )
    parser_resources_create.add_argument(
        "-d",
        "--data",
        help="Resource data, as ex: '{\"age\": 23}'",
    )
    parser_resources_create.set_defaults(func=resources_create_handler)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
