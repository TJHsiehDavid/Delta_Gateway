import sys 
import os
import time
import traceback
from datetime import datetime
import json
import base64
import copy


from pyaci.mesh import types as mt
from .properties import Proerties
from .dataDao import DataDao
import shutil

from .deviceService import DeviceService

class SensorFactory():

	_instance = None

	@staticmethod
	def get_instance():
		if SensorFactory._instance is None:
			SensorFactory()
		return SensorFactory._instance

	def __init__(self):
		self.beacon_map = {}
		self.beacon_name_map = {}

		SensorFactory._instance = self

	def addBeaconData(self, data):
		
		src = data.get("src")
		major_id = str(data.get("data_majorID"))
		minor_id = str(data.get("data_minorID"))
		data_rssi = data.get('data_rssi')

		akey = major_id + "|"  + minor_id

		if src is None or minor_id is None:
			return
		
		beacon_data = self.beacon_map.get(akey)
		if beacon_data == None	\
				or datetime.timestamp(datetime.now()) - datetime.timestamp(beacon_data["get_time"]) > 15 \
				or src == beacon_data["src"]:
			self.beacon_map[akey] = data
		elif int(beacon_data['data_rssi']) < data_rssi:
			self.beacon_map[akey] = data

	def getDataList(self):
		result = []
		for key, value in self.beacon_map.items():
			if datetime.timestamp(datetime.now()) - datetime.timestamp(value["get_time"]) <= 20:
				result_value = copy.deepcopy(value)
				result_value["get_time"] = result_value["get_time"].strftime("%H:%M:%S %f")
				result.append(result_value)
		return result

class SensorService():

	_instance = None

	@staticmethod
	def get_instance(deviceService):
		if SensorService._instance is None:
			SensorService(deviceService)
		return SensorService._instance

	def __init__(self, deviceService):
		self.ds = deviceService
		self.dataDao = DataDao.get_instance()
		self.sensor_factory = SensorFactory.get_instance()

		SensorService._instance = self


	def getSensorGroupByAddress(self, address):
		tList = [x for x in self.ds.db.sensor_groups if x.address.real == address]
		return  tList[0] if len(tList) > 0 else None

	def getNewSensorGroupId(self):
		if len(self.ds.db.sensor_groups) > 500:
			raise Exception("sensor group over 500!!")
		if len(self.ds.db.sensor_groups) > 0:
			return self.ds.db.sensor_groups[len(self.ds.db.sensor_groups) - 1].address + 10
		
		return DeviceService.DEFULT_SENSOR_GROUP_ID

	def getSensorGroupList(self):
		result = []
		for g in self.ds.db.sensor_groups:
			group_data = self.dataDao.getLight(g.address.real, DeviceService.TYPE_SENSOR_GROUP)
			result.append({"id":g.address,
							"name":g.name,
							"image": group_data["img_path"] if group_data is not None else ""}) 
		return result

	def getSensorGroup(self, id):
		
		group_obj = self.getSensorGroupByAddress(id)
		group_data = self.dataDao.getLight(id, DeviceService.TYPE_SENSOR_GROUP)	
			
		a_group = {"id" :group_obj.address,
					"name" : group_obj.name,
					"device" : [],
					"image" :group_data["img_path"]}

		for aNode in self.ds.db.nodes:
			node = {}
			node["id"] = aNode.unicast_address.real
			node["name"] = aNode.name
			node["inUse"] = True if aNode.unicast_address.real in group_obj.nodes_unicast_address else False
			a_group["device"].append(node)

		return a_group

				
	def addSensorGroup(self, name, device_list):
		
		new_group_id = self.getNewSensorGroupId()

		for light_id in device_list:
			unicast_address = int(light_id)
			light_data = self.dataDao.getLight(unicast_address, DeviceService.TYPE_SINGLE_LIGHT)
			a_node = self.ds.getNodeByUnicastAddress(unicast_address)
			if light_data == None or a_node == None:
				raise Exception('node not exist')
				
			self.ds.ccPublishSet(unicast_address)
			self.ds.model_add(a_node.unicast_address, 0, 0x1100)
			self.ds.model_add(a_node.unicast_address, 0, 0x1101)
			self.ds.model_add(a_node.unicast_address, new_group_id, 0x1100, DeviceService.TYPE_GROUP)
			self.ds.model_add(a_node.unicast_address, new_group_id, 0x1101, DeviceService.TYPE_GROUP)
			self.ds.model_publication_set(a_node.unicast_address, 0x1100, new_group_id)
			self.ds.model_publication_set(a_node.unicast_address, 0x1101, new_group_id)

		self.ds.db.sensor_groups.append(mt.Group(name, new_group_id, nodes_unicast_address=[int(x) for x in device_list]))
		
		self.ds.db.store()
		
		self.dataDao.saveLight(new_group_id, DeviceService.TYPE_SENSOR_GROUP, 0)

		return new_group_id
	
	def updateSensorGroup(self, id, name, device_list):
		
		group_obj = self.getSensorGroupByAddress(id)
		

		for light_id in device_list:
			unicast_address = int(light_id)
			
			if unicast_address in group_obj.nodes_unicast_address:
				continue

			a_node = self.ds.getNodeByUnicastAddress(unicast_address)
			if a_node == None:
				raise Exception('node not exist')
				
			self.ds.ccPublishSet(unicast_address)
			self.ds.model_add(a_node.unicast_address, 0, 0x1100)
			self.ds.model_add(a_node.unicast_address, 0, 0x1101)
			self.ds.model_add(a_node.unicast_address, id, 0x1100, DeviceService.TYPE_GROUP)
			self.ds.model_add(a_node.unicast_address, id, 0x1101, DeviceService.TYPE_GROUP)
			self.ds.model_publication_set(a_node.unicast_address, 0x1100, id)
			self.ds.model_publication_set(a_node.unicast_address, 0x1101, id)
			

		for light_id in group_obj.nodes_unicast_address:
			if str(light_id) in device_list:
				continue
			self.removeLightFormSensorGroup(light_id, id, group_obj)
			
		group_obj.name = name
		group_obj.nodes_unicast_address = [int(x) for x in device_list]		
		self.ds.db.store()

	def removeLightFormSensorGroup(self, light_id, group_id, group_obj):

		light_data = self.dataDao.getLight(light_id, DeviceService.TYPE_SINGLE_LIGHT)
		if light_data == None:
			return None

		a_node = self.ds.getNodeByUnicastAddress(light_id)
		if a_node == None:
			return None
		
		self.ds.ccPublishSet(light_id)
		self.ds.light_group_remove(a_node.unicast_address, group_id, 0x1100)
		self.ds.light_group_remove(a_node.unicast_address, group_id, 0x1101)


	def updateSensorGroupInfo(self, id, name, img_file):

		group_obj = self.getSensorGroupByAddress(id)
		group_data = self.dataDao.getLight(id, DeviceService.TYPE_SENSOR_GROUP)

		if img_file is not None:
			if group_data["img_path"] is not None:
				os.remove(DeviceService.IMG_PATH + group_data["img_path"])
			image_name = "G_" + str(datetime.now().timestamp())
			img_file.save(DeviceService.IMG_PATH + image_name)

			self.dataDao.updateLightImage(id, DeviceService.TYPE_SENSOR_GROUP, image_name)

		group_obj.name = name	
		self.ds.db.store()

	def deleteSensorGroup(self, id):
	
		group_obj = self.getSensorGroupByAddress(id)
		group_data = self.dataDao.getLight(id, DeviceService.TYPE_SENSOR_GROUP)

		for light_id in group_obj.nodes_unicast_address:
			self.removeLightFormSensorGroup(light_id, id, group_obj)
		
		if group_data["img_path"] is not None:
				os.remove(DeviceService.IMG_PATH + group_data["img_path"])
		
		for i in range(0, len(self.ds.db.sensor_groups)):
			if self.ds.db.sensor_groups[i].address == id:
				del self.ds.db.sensor_groups[i]
				break
		
		self.ds.db.store()
		self.dataDao.deleteLight(id, DeviceService.TYPE_SENSOR_GROUP)

	def getNewSensorId(self):
		sensor_data = self.dataDao.getMaxSensor()	
		if sensor_data == None:
			return 0
		return sensor_data["id"] + 1
	
	def addSensor(self, group_id_ary, cadence, uuid, major_range, minor_range):

		id = self.getNewSensorId()

		self.dataDao.saveSensor(id, uuid, major_range, minor_range, cadence)
		
		for group_id in group_id_ary:
			self.dataDao.saveSensorGroup(id, int(group_id))

		return id

	def updateSensor(self, sensor_id, new_group_id_ary, cadence, uuid, major_range, minor_range):

		group_id_ary = [int(x) for x in new_group_id_ary]

		sensor_group_data = self.dataDao.getSensorGroupList(sensor_id)

		ori_sensor_group_id_ary = [x["group_id"] for x in sensor_group_data]

		for group_id in group_id_ary:
			if group_id not in ori_sensor_group_id_ary:
				self.dataDao.saveSensorGroup(sensor_id, group_id)

		for group_id in ori_sensor_group_id_ary:
			if group_id not in group_id_ary:
				self.dataDao.deleteSensorGroup(sensor_id, group_id)

		self.dataDao.updateSensor(sensor_id, uuid, major_range, minor_range, cadence)
		
	def deleteSensor(self, sensor_id):
		self.dataDao.deleteSensorGroup(sensor_id)
		self.dataDao.deleteSensor(sensor_id)

	def getSensorList(self):
		sensor_list = self.dataDao.getSensorList()
		return [{"id":x["id"], "run" : True if self.ds.run_sensor == x["id"] else False} for x in sensor_list]

	def getSensor(self, sensor_id):
		sensor_data = self.dataDao.getSensor(sensor_id)
		sensor_group_data = self.dataDao.getSensorGroupList(sensor_id)

		result_map = {
			"id": sensor_data["id"],
			"v1" : sensor_data["v1"],
			"uuid" : sensor_data["uuid"],
			"major_range" : sensor_data["major_range"],
			"minor_range" : sensor_data["minor_range"],
			"groups":[],
		}

		for a_data in sensor_group_data:
			sensor_group_obj = self.getSensorGroupByAddress(a_data["group_id"])
			result_group = {
				"address" : sensor_group_obj.address,
				"name" : sensor_group_obj.name,
				"devices" : []
			}

			for light_id in sensor_group_obj.nodes_unicast_address:
				light_obj = self.ds.getNodeByUnicastAddress(light_id)
				result_group["devices"].append({
					"id": light_obj.unicast_address.real,
					"name" : light_obj.name
				})

			result_map["groups"].append(result_group)
		return result_map


	def runSensor(self, sensor_id, cadence):
		sensor_data = self.dataDao.getSensor(sensor_id)

		group_id_ary = self.dataDao.getSensorGroupList(sensor_id)

		if sensor_data == None:
			raise Exception("no find sensor")
		
		beacon_name_list = self.dataDao.getBeacons(uuid=sensor_data["uuid"])

		self.beacon_name_map = {}

		for a_data in beacon_name_list:
			a_key = str(a_data["major"]) + "|" + str(a_data["minor"])
			self.beacon_name_map[a_key] = a_data["name"]

		self.ds.startSensor(sensor_data, [x["group_id"] for x in group_id_ary], cadence)

	def stopSensor(self):
		self.ds.stopSensor()

	
	def getSensorStream(self):
		while self.ds.run_sensor != -1:
			time.sleep(0.01)
			result_list = self.ds.getSensorStreamData()
			if len(result_list) > 0:
				self.setBeaconName(result_list)
				yield 'data: {}\n\n'.format(json.dumps({"list":result_list}))

		return 'end'
	
	def getSensorStreamList(self):
		while self.ds.run_sensor != -1:
			time.sleep(0.1)
			data_map = self.ds.getSensorStreamObject()
			if len(data_map) > 0:
				for key, data in data_map.items():
					self.sensor_factory.addBeaconData(data)
				result_list = self.sensor_factory.getDataList()
				self.setBeaconName(result_list)
				result = {"list":result_list}
				yield 'data: {}\n\n'.format(json.dumps(result))

		return 'end'

	def setBeaconName(self, data_list):
		for a_data in data_list:
			a_key = a_data["data_majorID"] + "|" + a_data["data_minorID"]
			a_name = self.beacon_name_map.get(a_key) 
			a_data["beacon_name"] = a_name if a_name is not None else a_key