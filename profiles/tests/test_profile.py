import json
from django.core.urlresolvers import reverse
from app.utils import TestCaseEx
from profiles.models import Profile


class TestProfilesViews(TestCaseEx):
    def test_anyone_can_see_index_page(self):
        self.can_get("profiles.views.profile.index")

    def test_anyone_can_check_profile(self):
        p = Profile.objects.create(name=u"somename")
        self.can_get("profiles.views.profile.show", pargs=[p.pk])

    @TestCaseEx.superuser
    def test_logged_user_can_see_more_data(self):
        pass

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
    def test_simple_user_cant_update_without_passkey_in_session(self):
        p = Profile.objects.create(name=u"some_new_name")

        params = {
            'text': '1928laksldjas',
            'name': 'alsjdlaskdjlsd'
        }
        response = self.redirect_on_post("profiles.views.profile.update", params=params, pargs=[p.pk])


    # @TestCaseEx.login
    # def test_simple_user_should_provide_passkey_to_update(self):
    # pass

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


