"""
Management command to clean up duplicate users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction


class Command(BaseCommand):
    help = "Clean up duplicate users with the same email address"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Find duplicate emails
        from django.db.models import Count

        duplicate_emails = (
            User.objects.values("email")
            .annotate(count=Count("email"))
            .filter(count__gt=1)
        )

        if not duplicate_emails.exists():
            self.stdout.write(self.style.SUCCESS("No duplicate users found!"))
            return

        self.stdout.write(
            f"Found {duplicate_emails.count()} duplicate email addresses:"
        )

        total_deleted = 0

        for email_data in duplicate_emails:
            email = email_data["email"]
            users = User.objects.filter(email=email).order_by("date_joined")

            self.stdout.write(f"\nEmail: {email}")
            self.stdout.write(f"Users ({users.count()}):")

            # Keep the first (oldest) user, delete the rest
            keep_user = users.first()
            delete_users = users[1:]

            self.stdout.write(
                f"  KEEP: ID {keep_user.id}, Username: {keep_user.username}, Created: {keep_user.date_joined}"
            )

            for user in delete_users:
                self.stdout.write(
                    f"  DELETE: ID {user.id}, Username: {user.username}, Created: {user.date_joined}"
                )

                if not dry_run:
                    # Delete associated profile if exists
                    if hasattr(user, "profile"):
                        user.profile.delete()

                    # Delete the user
                    user.delete()
                    total_deleted += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDRY RUN: Would delete {len(delete_users)} duplicate users"
                )
            )
            self.stdout.write("Run without --dry-run to actually delete the duplicates")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSuccessfully deleted {total_deleted} duplicate users!"
                )
            )
