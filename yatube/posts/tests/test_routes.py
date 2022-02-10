from django.test import TestCase
from django.urls import reverse


SLUG = "testslug"
USERNAME = "Abraham"
POST_ID = 1


class RoutesTest(TestCase):
    def test_routes(self):
        set = [
            ["index", [], "/"],
            ["group_list", [SLUG], f"/group/{SLUG}/"],
            ["post_create", [], "/create/"],
            ["profile", [USERNAME], f"/profile/{USERNAME}/"],
            ["post_detail", [POST_ID], f"/posts/{POST_ID}/"],
            ["post_edit", [POST_ID], f"/posts/{POST_ID}/edit/"],
            ["add_comment", [POST_ID], f"/posts/{POST_ID}/comment/"]
        ]

        for route, arg, url in set:
            self.assertEqual(reverse(f"posts:{route}", args=arg), url)
