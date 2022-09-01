from django.test import Client, TestCase


class ErrorPageURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_404_page_correct_template(self):
        response = self.guest_client.get('/fdfds')
        self.assertTemplateUsed(response, 'core/404.html')
