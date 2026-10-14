"""Operator-only account provisioning; passwords never appear in argv or stdout."""
import argparse
import getpass

from app.services.auth_service import get_auth_store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['create', 'reset-password', 'disable', 'enable', 'revoke', 'set-role', 'cleanup'])
    parser.add_argument('--username')
    parser.add_argument('--role', choices=['marketing', 'sales', 'super_admin'])
    args = parser.parse_args()
    store = get_auth_store()
    if args.action == 'cleanup':
        store.cleanup()
        print('Expired auth sessions and login buckets cleaned.')
        return
    if not args.username:
        parser.error('--username is required')
    if args.action in {'create', 'set-role'} and not args.role:
        parser.error('--role is required')
    password = None
    if args.action in {'create', 'reset-password'}:
        password = getpass.getpass('Password (15–128 characters): ')
        if password != getpass.getpass('Confirm password: '):
            parser.error('Passwords do not match')
    try:
        if args.action == 'create':
            store.create_user(args.username, password, args.role)
        else:
            store.update_user(args.username, password=password,
                              active={'enable': True, 'disable': False}.get(args.action),
                              role=args.role if args.action == 'set-role' else None)
    except ValueError as exc:
        parser.error(str(exc))
    print(f'Account {args.action} completed. Existing sessions revoked for account updates.')


if __name__ == '__main__':
    main()
