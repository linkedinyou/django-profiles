import json
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from app.utils import TestCaseEx
from profiles.models import Profile, ProfilePasskeys
from profiles.views.profile import session_passkeys


class TestProfilesViews(TestCaseEx):

    def test_anyone_can_see_index_page(self):
        # everyone can see profiles without passkeys
        p1 = Profile.objects.create(name=u"a;sldjalk sjm900q ufasjflk aks")
        p2 = Profile.objects.create(name=u"j iosdiaus0d aus08h32ea;ldi ")
        p3 = Profile.objects.create(name=u";la sk d;lasjdlk hask;dj")

        response = self.can_get("profiles.views.profile.index")
        self.assertContains(response, p1.name)
        self.assertContains(response, p2.name)
        self.assertContains(response, p3.name)

        Alice = User.objects.create_user("Alice", password="Alice")
        Bob = User.objects.create_user("Bob", password="Bob")

        # logged users as well can see all profiles without passkeys
        self.client.login(username="Alice", password="Alice")
        response = self.can_get("profiles.views.profile.index")
        self.assertContains(response, p1.name)
        self.assertContains(response, p2.name)
        self.assertContains(response, p3.name)

        # but Alice canT see profiles assigned to Bob
        ProfilePasskeys.objects.create(user=Bob, profile=p1)
        response = self.can_get("profiles.views.profile.index")
        self.assertNotContains(response, p1.name)
        self.assertContains(response, p2.name)
        self.assertContains(response, p3.name)

        self.client.logout()

        # while Bob CAN see all profiles
        self.client.login(username="Bob", password="Bob")
        response = self.can_get("profiles.views.profile.index")
        self.assertContains(response, p1.name)
        self.assertContains(response, p2.name)
        self.assertContains(response, p3.name)

        self.client.logout()

        # guest cant see profiles with passkeys
        ProfilePasskeys.objects.create(user=Alice, profile=p3)
        response = self.can_get("profiles.views.profile.index")
        self.assertNotContains(response, p1.name)
        self.assertContains(response, p2.name)
        self.assertNotContains(response, p3.name)

        # while superuser always CAN see all profiles
        self.client.login(username=self.root.username, password=self.password)
        response = self.can_get("profiles.views.profile.index")
        self.assertContains(response, p1.name)
        self.assertContains(response, p2.name)
        self.assertContains(response, p3.name)

        self.client.logout()

    def test_index_admin_can_see_only_profiles_which_he_admins_public_profiles_and_those_to_which_he_has_passkey(self):
        ProfilePasskeys.objects.all().delete()
        user = User.objects.create_user(username="C", password="C")
        anotherUser = User.objects.create_user(username="D", password="D")

        userprofile = user.profile
        userprofile.is_admin = True
        userprofile.save()

        publicProfile = Profile.objects.create(name=u"a;sldjalk sjm900q ufasjflk aks")
        assocciatedProfile = Profile.objects.create(name=u"j iosdiaus0d aus08h32ea;ldi ")
        administratedProfile = Profile.objects.create(name=u";la sk d;lasjdlk hask;dj")
        anotherUserProfile = Profile.objects.create(name=u";la sk alksjdlaskjdolkasdj")

        # setup profiles
        ProfilePasskeys.objects.create(user=user, profile=assocciatedProfile)
        ProfilePasskeys.objects.create(user=anotherUser, profile=anotherUserProfile)
        userprofile.profiles.add(administratedProfile)

        self.client.login(username=user.username, password=user.username)

        response = self.can_get("profiles.views.profile.index")
        self.assertContains(response, publicProfile.name)
        self.assertContains(response, assocciatedProfile.name)
        self.assertContains(response, administratedProfile.name)
        self.assertNotContains(response, anotherUserProfile.name)

        self.client.logout()


    def test_if_profile_dont_have_users_anyone_can_see_it(self):
        p = Profile.objects.create()
        self.can_get("profiles.views.profile.show", pargs=[p.pk])

    def test_if_profile_have_associated_users_only_they_can_see_it(self):
        p = Profile.objects.create()
        user = User.objects.create_user("user2", password="123")
        ProfilePasskeys.objects.create(user=user, profile=p, passkey="coolpasskey")

        # guest cant see that profile
        self.redirect_to_login_on_get("profiles.views.profile.show", pargs=[p.pk])

        # associated user cant without provided passkey
        self.client.login(username=user, password="123")
        response = self.redirect_on_get("profiles.views.profile.show", pargs=[p.pk])
        self.assertRedirects(response, reverse("profiles.views.profile.provide_passkey", args=[p.pk]))
        self.client.logout()

        # but associated user can with correct passkey
        self.client.login(username=user, password="123")
        session = self.client.session
        session[session_passkeys] = {
            p.id: "coolpasskey"
        }
        session.save()

        self.can_get("profiles.views.profile.show", pargs=[p.pk])
        #user dont need to enter password two times
        self.can_get("profiles.views.profile.show", pargs=[unicode(p.pk)])

        self.client.logout()


    def test_if_profile_have_associated_users_they_should_provide_passkey_to_view_it(self):
        p = Profile.objects.create()
        user = User.objects.create_user("user2", password="123")
        ProfilePasskeys.objects.create(user=user, profile=p)

    @TestCaseEx.superuser
    def test_superuser_can_see_all_profiles(self):
        p = Profile.objects.create()
        user = User.objects.create_user("user3", password="123")
        ProfilePasskeys.objects.create(user=user, profile=p)

        self.can_get("profiles.views.profile.show", pargs=[p.pk])

    def test_guest_cant_add(self):
        self.redirect_on_post("profiles.views.profile.add")
        self.redirect_on_get("profiles.views.profile.add")

    @TestCaseEx.login
    def test_simple_user_cant_add(self):
        self.redirect_on_post("profiles.views.profile.add")
        self.redirect_on_get("profiles.views.profile.add")

    @TestCaseEx.superuser
    def test_adding_should_create_new_profile(self):
        self.can_get("profiles.views.profile.add")  # check that we can get add page

        count_before = Profile.objects.count()
        params = {
            'text': '1928laksldjas',
            'name': 'alsjdlaskdjlsd'
        }
        response = self.redirect_on_post("profiles.views.profile.add", params)

        self.assertEqual(count_before + 1, Profile.objects.count())
        new_profile = Profile.objects.order_by("-pk").first()
        self.assertEqual(new_profile.text, params['text'])
        self.assertEqual(new_profile.name, params['name'])

        self.assertRedirects(response, reverse("profiles.views.profile.show_by_slug", args=[new_profile.slug]))

    @TestCaseEx.superuser
    def test_adding_with_ajax_should_create_new_profile(self):
        count_before = Profile.objects.count()
        params = {
            'text': '1928laksldjas',
            'name': 'alsjdlaskdjlsd'
        }
        response = self.can_post("profiles.views.profile.add", params, ajax=True)
        self.assertEqual(count_before + 1, Profile.objects.count())

        data = json.loads(response.content)

        new_profile = Profile.objects.order_by("-pk").first()
        self.assertEqual(data['fields']['text'], params['text'])
        self.assertEqual(int(data['pk']), new_profile.pk)
        self.assertEqual(new_profile.text, params['text'])
        self.assertEqual(data['fields']['name'], params['name'])
        self.assertEqual(new_profile.name, params['name'])

    def test_guest_cant_update(self):
        p = Profile.objects.create(name=u"some_new_name")
        params = {
            'text': '1928laksldjas',
            'name': 'alsjdlaskdjlsd'
        }
        self.redirect_on_post("profiles.views.profile.update", pargs=[p.pk], params=params)
        self.redirect_on_get("profiles.views.profile.update", pargs=[p.pk], params=params)

    @TestCaseEx.login
    def test_simple_user_cant_update(self):
        p = Profile.objects.create(name=u"some_another_new_name")
        ProfilePasskeys.objects.all().delete()
        ProfilePasskeys.objects.create(user=self.user, profile=p, passkey="5678")
        params = {
            'text': '1928laksldjas',
            'name': 'alsjdlaskdjlsd'
        }
        # self.redirect_to_login_on_get("profiles.views.profile.update", pargs=[p.pk], params=params)
        self.redirect_to_login_on_post("profiles.views.profile.update", pargs=[p.pk], params=params)

    def test_admin_cant_update_not_his_profiles(self):
        adminUser = User.objects.create_user("alkshdaklsd", password="234")

        p = Profile.objects.create(name=u"some_another_new_nam1231e")
        ProfilePasskeys.objects.all().delete()
        ProfilePasskeys.objects.create(user=adminUser, profile=p, passkey="5678")

        if self.client.login(username=adminUser, password="234"):

            session = self.client.session
            session[session_passkeys] = {
                p.id: "5678"
            }
            session.save()

            params = {
                'text': '1928laksldjas',
                'name': 'alsjdlaskdjlsd'
            }

            self.redirect_to_login_on_post("profiles.views.profile.update", params=params, pargs=[p.pk])
            self.redirect_to_login_on_get("profiles.views.profile.update", params=params, pargs=[p.pk])

            self.client.logout()

    def test_admin_can_update_his_profiles(self):
        adminUser = User.objects.create_user("alkshdakasdasdlsd", password="234")

        p = Profile.objects.create(name=u"some_another_new_nam1231e")

        userprofile = adminUser.profile
        userprofile.is_admin = True
        userprofile.profiles.add(p.pk)
        userprofile.save()

        if self.client.login(username=adminUser, password="234"):

            session = self.client.session
            session[session_passkeys] = {
                p.id: "5678"
            }
            session.save()

            params = {
                'text': '1928laksldjas',
                'name': 'alsjdlaskdjlsd'
            }

            self.can_get("profiles.views.profile.update", params=params, pargs=[p.pk])
            response = self.redirect_on_post("profiles.views.profile.update", params=params, pargs=[p.pk])

            p = Profile.objects.get(pk=p.pk)
            self.assertRedirects(response, reverse("profiles.views.profile.show_by_slug", args=[p.slug]))

            self.assertEqual(p.text, params['text'])
            self.assertEqual(p.name, params['name'])
            self.client.logout()


    @TestCaseEx.superuser
    def test_update_should_update_values(self):
        p = Profile.objects.create(name=u"some_new_name")

        self.can_get("profiles.views.profile.update", pargs=[p.pk])  # check that we can get update page

        params = {
            'text': '1928laksldjas',
            'name': 'alsjdlaskdjlsd'
        }
        response = self.redirect_on_post("profiles.views.profile.update", params=params, pargs=[p.pk])

        p = Profile.objects.get(pk=p.pk)
        self.assertRedirects(response, reverse("profiles.views.profile.show_by_slug", args=[p.slug]))

        self.assertEqual(p.text, params['text'])
        self.assertEqual(p.name, params['name'])

    @TestCaseEx.superuser
    def test_update_with_ajax_should_update_values(self):
        p = Profile.objects.create(name=u"some_new_name")

        params = {
            'text': '1928laksldjas',
            'name': 'alsjdlaskdjlsd'
        }
        response = self.can_post("profiles.views.profile.update", params=params, pargs=[p.pk], ajax=True)

        data = json.loads(response.content)
        p = Profile.objects.get(pk=p.pk)

        self.assertEqual(data['fields']['text'], params['text'])
        self.assertEqual(int(data['pk']), p.pk)
        self.assertEqual(p.text, params['text'])
        self.assertEqual(data['fields']['name'], params['name'])
        self.assertEqual(p.name, params['name'])

    def test_guest_cant_remove(self):
        p = Profile.objects.create(name=u"new item")
        self.redirect_on_post("profiles.views.profile.remove", pargs=[p.pk])
        self.redirect_on_get("profiles.views.profile.remove", pargs=[p.pk])

    @TestCaseEx.login
    def test_simple_user_cant_remove(self):
        p = Profile.objects.create(name=u"new item")
        self.redirect_on_post("profiles.views.profile.remove", pargs=[p.pk])
        self.redirect_on_get("profiles.views.profile.remove", pargs=[p.pk])

    @TestCaseEx.superuser
    def test_remove_should_remove_profile(self):
        p = Profile.objects.create(name=u"new item")
        self.assertEqual(1, Profile.objects.filter(pk=p.pk).count())

        response = self.redirect_on_get("profiles.views.profile.remove", pargs=[p.pk])
        self.assertRedirects(response, reverse("profiles.views.profile.index"))

        self.assertEqual(0, Profile.objects.filter(pk=p.pk).count())

    @TestCaseEx.superuser
    def test_remove_on_ajax_should_remove_profile(self):
        p = Profile.objects.create(name=u"new item")
        self.assertEqual(1, Profile.objects.filter(pk=p.pk).count())

        response = self.can_get("profiles.views.profile.remove", pargs=[p.pk], ajax=True)

        self.assertEqual(0, Profile.objects.filter(pk=p.pk).count())



