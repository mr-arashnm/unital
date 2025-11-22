from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from apps.accounts.models import User
from .models import Building, Unit, Parking, Warehouse


class ComplexesParkingWarehouseAPITest(TestCase):
	def setUp(self):
		# create a manager user
		self.manager = User.objects.create_user(
			email='mgr@example.com', password='pass1234', first_name='Mgr', last_name='One', user_type='manager'
		)

		# create building and unit
		self.building = Building.objects.create(
			name='Test Building', code='B001', type='residential', address='123 Test St',
			total_floors=5, total_units=10, total_parkings=20, total_warehouses=5, created_by=self.manager
		)

		self.unit = Unit.objects.create(building=self.building, floor=1, unit_number='101', area=50.0)

		self.client = APIClient()
		self.client.force_authenticate(user=self.manager)

	def test_create_and_patch_parking(self):
		url = reverse('building-parkings', kwargs={'building_id': self.building.id})
		data = {'floor': 1, 'code': 'P-1001', 'status': 'available'}
		resp = self.client.post(url, data, format='json')
		self.assertEqual(resp.status_code, 201)
		self.assertEqual(Parking.objects.filter(code='P-1001').exists(), True)

		parking = Parking.objects.get(code='P-1001')
		detail_url = reverse('building-parking-detail', kwargs={'building_id': self.building.id, 'parking_id': parking.id})
		patch_resp = self.client.patch(detail_url, {'status': 'occupied', 'unit': self.unit.id}, format='json')
		self.assertEqual(patch_resp.status_code, 200)
		parking.refresh_from_db()
		self.assertEqual(parking.status, 'occupied')
		self.assertEqual(parking.unit.id, self.unit.id)

	def test_create_and_patch_warehouse(self):
		url = reverse('building-warehouses', kwargs={'building_id': self.building.id})
		data = {'floor': 1, 'code': 'W-2001', 'status': 'available', 'area': 12.5}
		resp = self.client.post(url, data, format='json')
		self.assertEqual(resp.status_code, 201)
		self.assertEqual(Warehouse.objects.filter(code='W-2001').exists(), True)

		warehouse = Warehouse.objects.get(code='W-2001')
		detail_url = reverse('building-warehouse-detail', kwargs={'building_id': self.building.id, 'warehouse_id': warehouse.id})
		patch_resp = self.client.patch(detail_url, {'status': 'occupied', 'unit': self.unit.id}, format='json')
		self.assertEqual(patch_resp.status_code, 200)
		warehouse.refresh_from_db()
		self.assertEqual(warehouse.status, 'occupied')
		self.assertEqual(warehouse.unit.id, self.unit.id)

	def test_change_unit_residency(self):
		# create a resident user to transfer to
		resident = User.objects.create_user(email='res@example.com', password='pass1234', first_name='Res', last_name='One', user_type='resident')
		url = reverse('change_unit_residency', kwargs={'unit_id': self.unit.id})
		data = {'new_resident_id': resident.id, 'transfer_date': '2025-11-20'}
		resp = self.client.post(url, data, format='json')
		self.assertEqual(resp.status_code, 200)
		self.unit.refresh_from_db()
		self.assertEqual(self.unit.resident.id, resident.id)
