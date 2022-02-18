from django.test import TestCase
from django.urls import reverse

from posts.urls import app_name

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
            ["add_comment", [POST_ID], f"/posts/{POST_ID}/comment/"],
            ["follow_index", [], "/follow/"],
            ["profile_follow", [USERNAME], f"/profile/{USERNAME}/follow/"],
            ["profile_unfollow", [USERNAME], f"/profile/{USERNAME}/unfollow/"],
        ]

        for route, arg, url in set:
            self.assertEqual(reverse(f"{app_name}:{route}", args=arg), url)
