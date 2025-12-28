from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings


class Command(BaseCommand):
    help = "Set up Google and LinkedIn OAuth applications"

    def add_arguments(self, parser):
        parser.add_argument(
            "--google-client-id",
            type=str,
            help="Google OAuth Client ID",
        )
        parser.add_argument(
            "--google-client-secret",
            type=str,
            help="Google OAuth Client Secret",
        )
        parser.add_argument(
            "--linkedin-client-id",
            type=str,
            help="LinkedIn OAuth Client ID",
        )
        parser.add_argument(
            "--linkedin-client-secret",
            type=str,
            help="LinkedIn OAuth Client Secret",
        )

    def handle(self, *args, **options):
        # Get the current site
        site = Site.objects.get_current()

        # Set up Google OAuth
        if options["google_client_id"] and options["google_client_secret"]:
            google_app, created = SocialApp.objects.get_or_create(
                provider="google",
                name="Google",
                defaults={
                    "client_id": options["google_client_id"],
                    "secret": options["google_client_secret"],
                },
            )
            if not created:
                google_app.client_id = options["google_client_id"]
                google_app.secret = options["google_client_secret"]
                google_app.save()

            google_app.sites.add(site)
            self.stdout.write(
                self.style.SUCCESS("Google OAuth application configured successfully")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Google OAuth credentials not provided. Skipping Google setup."
                )
            )

        # Set up LinkedIn OAuth
        if options["linkedin_client_id"] and options["linkedin_client_secret"]:
            linkedin_app, created = SocialApp.objects.get_or_create(
                provider="linkedin_oauth2",
                name="LinkedIn",
                defaults={
                    "client_id": options["linkedin_client_id"],
                    "secret": options["linkedin_client_secret"],
                },
            )
            if not created:
                linkedin_app.client_id = options["linkedin_client_id"]
                linkedin_app.secret = options["linkedin_client_secret"]
                linkedin_app.save()

            linkedin_app.sites.add(site)
            self.stdout.write(
                self.style.SUCCESS("LinkedIn OAuth application configured successfully")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "LinkedIn OAuth credentials not provided. Skipping LinkedIn setup."
                )
            )

        self.stdout.write(self.style.SUCCESS("Social authentication setup completed!"))
