from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.complexes.models import Building, Unit, Feature


class SupportTicketFeatureTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		# create a user
		self.user = User.objects.create_user(
			email='user@example.com',
			password='pass',
			first_name='Test',
			last_name='User',
			user_type='resident'
		)
		# create a building without the support_tickets feature
		self.building = Building.objects.create(
			name='B1', code='B1', type='residential', address='Addr',
			total_floors=1, total_units=1, total_parkings=0, total_warehouses=0,
			created_by=self.user
		)
		# create a unit
		self.unit = Unit.objects.create(building=self.building, floor=1, unit_number='1A', area=50.0)

	def test_cannot_create_ticket_when_feature_disabled(self):
		self.client.force_authenticate(self.user)
		url = '/support-tickets/'
		data = {
			'unit': self.unit.id,
			'title': 'Leaky faucet',
			'description': 'The faucet is leaking'
		}
		resp = self.client.post(url, data, format='json')
		self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

	def test_can_create_ticket_when_feature_enabled(self):
		# add the feature to the building
		f, _ = Feature.objects.get_or_create(key='support_tickets', name='Support Tickets')
		self.building.features.add(f)

		self.client.force_authenticate(self.user)
		url = '/support-tickets/'
		data = {
			'unit': self.unit.id,
			'title': 'Broken window',
			'description': 'Window broken'
		}
		resp = self.client.post(url, data, format='json')
		self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
