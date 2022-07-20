import sys 
import os
import time
import sqlite3

from flask import Flask

app = Flask(__name__)

this_file_dir = os.path.dirname(os.path.abspath(__file__))

class DataDao:
	
	_instance = None
	
	DATA_BASE_NAME = this_file_dir + '/../lights'
	
	@staticmethod
	def get_instance():
		if DataDao._instance is None:
			DataDao()
		return DataDao._instance

	@staticmethod
	def clear():
		if DataDao._instance is not None:
			DataDao._instance.closeConnection()
			DataDao._instance = None

	def __init__(self):
		
		self.conn = None
	
		if DataDao._instance is not None:
			raise Exception('only one instance can exist')
		else:
			DataDao._instance = self
		
		self.doInitDB()
	
	def getConn(self):
		self.closeConnection()
		return sqlite3.connect(DataDao.DATA_BASE_NAME, check_same_thread=False)
		
	def doInitDB(self):
		self.conn = self.getConn()
		
		with app.open_resource('config', mode='r') as f:
			self.conn.cursor().executescript(f.read())

		self.conn.commit()
		
	def saveLight(self, id, light_type, is_temperature):
		self.conn.cursor().execute("INSERT INTO lights (id, light_type, is_temperature) VALUES (?, ?, ?)", 
				(id, light_type, is_temperature))  
		self.conn.commit()
		
	def updateLightImage(self, id, light_type, img_name):
		self.conn.cursor().execute("update lights  set img_path = ? where id = ? and light_type = ?", 
				(img_name, id, light_type))  
		self.conn.commit()

	def updateLight(self, id, light_type, is_temperature):
		self.conn.cursor().execute("update lights  set is_temperature = ? where id = ? and light_type = ?", 
				(is_temperature, id, light_type))  
		self.conn.commit()
		
	def getLight(self, id, light_type):
		lights = self.conn.cursor().execute("SELECT * FROM lights WHERE light_type = ? and id = ?", (light_type,id))
		colname = [ d[0] for d in lights.description ]
		light_list = [ dict(zip(colname, r)) for r in lights.fetchall() ]
		return light_list[0] if len(light_list) > 0 else None
		
	def queryLights(self, light_type):
		lights = self.conn.cursor().execute("SELECT * FROM lights WHERE light_type = ? ", (light_type,))
		colname = [ d[0] for d in lights.description ]
		return [ dict(zip(colname, r)) for r in lights.fetchall() ]
		
	def deleteLight(self, id, light_type):
		self.conn.cursor().execute("DELETE FROM lights where id = ? and light_type = ? ", (id, light_type))
		self.conn.commit()

		## delete relationship table
		self.conn.cursor().execute("DELETE FROM scene_light_status where light_id = ? and light_type = ? ", (id, light_type))
		self.conn.commit()

		if light_type == 3:
			self.conn.cursor().execute("DELETE FROM sensor_light_status where light_id = ?", (id, ))
			self.conn.commit()

		if light_type == 1:
			self.conn.cursor().execute("DELETE FROM schedules where light_id = ? and schedule_type = ?", (id, light_type))
			self.conn.commit()

		if light_type == 1:
			self.deleteLightSceneRelation(light_id = id)
			# self.deleteLightScheduleRelation(light_id = id)

		if light_type == 3:
			self.deleteLightSceneRelation(group_id = id)
			# self.deleteLightScheduleRelation(group_id = id)
		
	def clearAll(self):
		self.conn.cursor().execute("DELETE FROM lights")
		self.conn.commit()
		
		self.conn.cursor().execute("DELETE FROM scenes")
		self.conn.commit()
		
		self.conn.cursor().execute("DELETE FROM scene_light_status")
		self.conn.commit()

		self.conn.cursor().execute("DELETE FROM sensors")
		self.conn.commit()
		
		self.conn.cursor().execute("DELETE FROM sensor_light_status")
		self.conn.commit()

		self.conn.cursor().execute("DELETE FROM schedules")
		self.conn.commit()

		self.conn.cursor().execute("DELETE FROM light_scene_relation")
		self.conn.commit()

		# 廢棄不用此table 20211015
		# self.conn.cursor().execute("DELETE FROM light_schedule_relation")
		# self.conn.commit()
		
	def closeConnection(self):
		if self.conn is not None:
			self.conn.close()
			self.conn = None
			
	def querySenceList(self):
		lights = self.conn.cursor().execute("SELECT * FROM scenes ORDER BY id")
		colname = [ d[0] for d in lights.description ]
		return [ dict(zip(colname, r)) for r in lights.fetchall() ]
	
	def saveScene(self, id, name, aTime, aLevel, img_path):
		self.conn.cursor().execute("INSERT INTO scenes (id, scene_name, scene_time, scene_level, img_path) VALUES (?, ?, ?, ?, ?)", 
				(id, name, aTime, aLevel, img_path))  
		self.conn.commit()
		
	def saveSceneLightStatus(self, scene_id, light_id, light_type,  state, lightness, temperature):
		self.conn.cursor().execute("INSERT INTO scene_light_status (scene_id, light_id, light_type, on_off, lightness, temperature) VALUES (?, ?, ?, ?, ?, ?)", 
				(scene_id, light_id, light_type, 1 if state else 0, lightness, temperature))  
		self.conn.commit()
	
	def updateScene(self, id, name, aTime, aLevel,img_path):
		self.conn.cursor().execute("UPDATE scenes set scene_name = ?, scene_time = ?, scene_level = ?, img_path = ? where id = ?", 
				(name, aTime, aLevel, img_path, id))  
		self.conn.commit()
		
	def updateSceneLightStatus(self, scene_id, light_id, light_type,  state, lightness, temperature):
		self.conn.cursor().execute("update scene_light_status set light_type = ?, on_off = ?, lightness = ?, temperature = ? where scene_id = ? and light_id = ?", 
				(light_type, 1 if state else 0, lightness, temperature, scene_id, light_id))  
		self.conn.commit()	
	
	def getSceneByLightId(self, light_id, scene_id):
		data = self.conn.cursor().execute(("SELECT DISTINCT t1.* FROM scenes as t1 "
											"inner join scene_light_status as t2 "
											"on t1.id = t2.scene_id "
											"where t2.light_id = ? and t2.scene_id = ? ORDER BY id"), (light_id, scene_id))
		colname = [ d[0] for d in data.description ]
		data_list = [ dict(zip(colname, r)) for r in data.fetchall() ]
		return data_list[0] if len(data_list) > 0 else None
		
	def getSceneByGroups(self, groups):
		sql=("SELECT DISTINCT t1.* FROM scenes as t1 "
			"inner join scene_light_status as t2 "
			"on t1.id = t2.scene_id "
			"where t2.light_id in ({seq})").format(seq=','.join(['?']*len(groups)))
		lights = self.conn.cursor().execute(sql, groups)
		colname = [ d[0] for d in lights.description ]
		return [ dict(zip(colname, r)) for r in lights.fetchall() ]

	# def queryAllScheduleRelationList(self):
	# 	data = self.conn.cursor().execute("SELECT * FROM light_schedule_relation ")
	# 	colname = [d[0] for d in data.description]
	# 	return [dict(zip(colname, r)) for r in data.fetchall()]

	# def queryScheduleRelationListForSetting(self,scene_id, light_type):
	# 	if light_type == 3:
	# 		data = self.conn.cursor().execute("SELECT distinct group_id,schedule_id FROM light_schedule_relation where scene_id = ? and group_id > 0 ",
	# 										  (scene_id,))
	# 	else:
	# 		data = self.conn.cursor().execute("SELECT distinct light_id,schedule_id FROM light_schedule_relation where scene_id = ? and group_id = 0 ",
	# 										  (scene_id,))
	#
	# 	colname = [d[0] for d in data.description]
	# 	return [dict(zip(colname, r)) for r in data.fetchall()]

	def querySceneLightStatusList(self, scene_id, light_type = 3):
		
		data = []
	
		if light_type == None:
			data = self.conn.cursor().execute("SELECT * FROM scene_light_status where scene_id = ? ", 
				(scene_id,))
		else:
			data = self.conn.cursor().execute("SELECT * FROM scene_light_status where scene_id = ? and light_type = ?", 
						(scene_id, light_type))
		colname = [ d[0] for d in data.description ]
		return [ dict(zip(colname, r)) for r in data.fetchall() ]
	
	def getSceneLightStatus(self, scene_id, light_id):
		
		data = self.conn.cursor().execute("SELECT * FROM scene_light_status where scene_id = ? and light_id = ?", 
				(scene_id, light_id))
		colname = [ d[0] for d in data.description ]
		data_list = [ dict(zip(colname, r)) for r in data.fetchall() ]
		return data_list[0] if len(data_list) > 0 else None
	
	def deleteSceneLightStatus(self, scene_id, light_id = None, light_type = None):

		sql = "DELETE FROM scene_light_status where scene_id = ? "
					
		params = [scene_id]

		if light_id != None:
			sql = sql + " and light_id = ? and light_type = ? "
			params.append(light_id)
			params.append(light_type)

		self.conn.cursor().execute(sql, tuple(params))
		self.conn.commit()
		
	def deleteScene(self, id):
		self.conn.cursor().execute("DELETE FROM scenes where id = ? ",
					(id,))
		self.conn.commit()
	
	def getScene(self, id):
		data = self.conn.cursor().execute("SELECT * FROM scenes WHERE id = ?", (id,))
		
		colname = [ d[0] for d in data.description ]
		data_list = [ dict(zip(colname, r)) for r in data.fetchall() ]
		return data_list[0] if len(data_list) > 0 else None
		
	def getLastSensor(self):
		data = self.conn.cursor().execute("SELECT * FROM sensors order by id  desc")
		
		colname = [ d[0] for d in data.description ]
		data_list = [ dict(zip(colname, r)) for r in data.fetchall() ]
		return data_list[0] if len(data_list) > 0 else None

	def saveSensorGroup(self, sensor_id, group_id):
		self.conn.cursor().execute("INSERT INTO sensor_groups (sensor_id, group_id) VALUES (?, ?)", 
				(sensor_id, group_id))  
		self.conn.commit()

	def saveSensor(self, id, uuid, major_range, minor_range, v1):
		self.conn.cursor().execute(("INSERT INTO sensors (id, uuid, major_range, minor_range, v1) "
				"VALUES (?, ?, ?, ?, ?)"), 
				(id, uuid, major_range, minor_range, v1))  
		self.conn.commit()

	def updateSensor(self, id, uuid, major_range, minor_range, v1):
		self.conn.cursor().execute(("UPDATE sensors "
					"set uuid = ?, major_range = ?, minor_range = ?, v1 = ? "
					"where id = ?"),
				(uuid, major_range, minor_range, v1, id))  
		self.conn.commit()

	def getSensorList(self):
		data = self.conn.cursor().execute("SELECT * FROM sensors order by id")
		colname = [ d[0] for d in data.description ]
		return [ dict(zip(colname, r)) for r in data.fetchall() ]


	def getSensor(self, id):
		data = self.conn.cursor().execute("SELECT * FROM sensors where id = ?", (id,))
		
		colname = [ d[0] for d in data.description ]
		data_list = [ dict(zip(colname, r)) for r in data.fetchall() ]
		return data_list[0] if len(data_list) > 0 else None

	def deleteSensor(self, id):
		sql = "DELETE FROM sensors where id = ? "
		params = [id]

		self.conn.cursor().execute(sql, tuple(params))
		self.conn.commit()

	def getSensorGroupList(self, sensor_id):
		data = self.conn.cursor().execute("SELECT * FROM sensor_groups where sensor_id = ? ", 
						(sensor_id,))
		colname = [ d[0] for d in data.description ]
		return [ dict(zip(colname, r)) for r in data.fetchall() ]

	def deleteSensorGroup(self, sensor_id, group_id = None):
		sql = "DELETE FROM sensor_groups where sensor_id = ? "
					
		params = [sensor_id]

		if group_id is not None:
			sql = sql + " and group_id = ? "
			params.append(group_id)

		self.conn.cursor().execute(sql, tuple(params))
		self.conn.commit()
	
	def getLightScheduleList(self, light_id):
		data = self.conn.cursor().execute("SELECT * FROM schedules where light_id = ? and schedule_type = 1 ", 
						(light_id,))
		colname = [ d[0] for d in data.description ]
		return [ dict(zip(colname, r)) for r in data.fetchall() ]

	def getSceneScheduleList(self):
		data = self.conn.cursor().execute("SELECT * FROM schedules where schedule_type = 5")
		colname = [ d[0] for d in data.description ]
		return [ dict(zip(colname, r)) for r in data.fetchall() ]

	def queryMaxScheduleId(self):
		data = self.conn.cursor().execute("SELECT id FROM schedules order by id desc")
		colname = [ d[0] for d in data.description ]
		data_list = [ dict(zip(colname, r)) for r in data.fetchall() ]
		return data_list[0] if len(data_list) > 0 else None

	def getLightSchedule(self, light_id, id):
		data = self.conn.cursor().execute(("SELECT * FROM schedules "
				"where id = ? and light_id = ?"), (id, light_id))
		
		colname = [ d[0] for d in data.description ]
		data_list = [ dict(zip(colname, r)) for r in data.fetchall() ]
		return data_list[0] if len(data_list) > 0 else None

	def getSceneSchedule(self, id):
		data = self.conn.cursor().execute(("SELECT ss1.*, s2.* FROM schedules as ss1 "
				"inner join scenes as s2 on ss1.scene_id = s2.id "
				"where ss1.id = ?"), (id,))
		
		colname = [ d[0] for d in data.description ]
		data_list = [ dict(zip(colname, r)) for r in data.fetchall() ]
		return data_list[0] if len(data_list) > 0 else None

	#
	def getScheduleById(self, id):
		data = self.conn.cursor().execute(("SELECT * FROM schedules "
										   "where id = ?"), (id,))

		colname = [d[0] for d in data.description]
		data_list = [dict(zip(colname, r)) for r in data.fetchall()]
		return data_list[0] if len(data_list) > 0 else None


	def saveSchedule(self, id, schedule_id,  schedule_type, light_id, scene_id, schedule_name, schedule_action, week, hour, mins):
		self.conn.cursor().execute(("INSERT INTO schedules (id, schedule_id, schedule_type, light_id, scene_id, schedule_name, schedule_action, week, hour, mins)"
						 "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"), 
						(id, schedule_id, schedule_type, light_id, scene_id, schedule_name, schedule_action, week, hour, mins))  
		self.conn.commit()

	def updateSchedule(self, id, schedule_name, schedule_action, week, hour, mins):
		self.conn.cursor().execute("UPDATE schedules set schedule_name = ?, schedule_action = ?, week = ?, hour = ?, mins = ? where id = ? ", 
				(schedule_name, schedule_action, week, hour, mins, id))  
		self.conn.commit()

	def deleteSchedule(self, schedule_id):
		self.conn.cursor().execute(("DELETE FROM schedules "
					"where id = ?"), (schedule_id,))
		self.conn.commit()

	def deleteAllSchedule(self, schedule_id):

		self.conn.cursor().execute("DELETE FROM schedules")
		self.conn.commit()

		# self.conn.cursor().execute("DELETE FROM light_schedule_relation")
		# self.conn.commit()

	def getLightSceneRelationList(self, light_id = None, scene_id = None):

		sql = ("SELECT distinct t1.scene_id, t2.scene_name FROM light_scene_relation as t1 "
						"left join scenes as t2 on t1.scene_id = t2.id where light_id = ? ")
					
		params = [light_id]

		data = self.conn.cursor().execute(sql, tuple(params))
		colname = [ d[0] for d in data.description ]
		return [ dict(zip(colname, r)) for r in data.fetchall() ]

	def getLightSceneRelationLisBySceneId(self, scene_id):

		sql = ("SELECT light_id, group_id, scene_id FROM light_scene_relation "
						"where scene_id = ? ")
					
		params = [scene_id]

		data = self.conn.cursor().execute(sql, tuple(params))
		colname = [ d[0] for d in data.description ]
		return [ dict(zip(colname, r)) for r in data.fetchall() ]
	

	# def getLightScheduleRelationList(self, light_id):
	#
	# 	sql = ("SELECT distinct schedule_id FROM light_schedule_relation "
	# 					" where light_id = ? ")
	#
	# 	params = [light_id]
	#
	# 	data = self.conn.cursor().execute(sql, tuple(params))
	# 	colname = [ d[0] for d in data.description ]
	# 	return [ dict(zip(colname, r)) for r in data.fetchall() ]

	def deleteLightSceneRelation(self, light_id = None, group_id = None, scene_id = None):

		sql = "DELETE FROM light_scene_relation where 1=1 "

		params = []

		if light_id != None:
			sql = sql + " and light_id = ? "
			params.append(light_id)

		if group_id != None:
			sql = sql + " and group_id = ? "
			params.append(group_id)

		if scene_id != None:
			sql = sql + " and scene_id = ? "
			params.append(scene_id)

		self.conn.cursor().execute((sql), tuple(params))
		self.conn.commit()

	def saveLightSceneRelation(self, light_id, group_id, scene_id):
		self.conn.cursor().execute(("INSERT INTO light_scene_relation (light_id, group_id, scene_id)"
						 "VALUES (?, ?, ?)"), 
						(light_id, group_id, scene_id))  
		self.conn.commit()

	# def saveLightScheduleRelation(self, light_id, group_id, scene_id, schedule_id):
	# 	self.conn.cursor().execute(("INSERT INTO light_schedule_relation (light_id, group_id, scene_id, schedule_id)"
	# 					 "VALUES (?, ?, ?, ?)"),
	# 					(light_id, group_id, scene_id, schedule_id))
	# 	self.conn.commit()

	# def deleteLightScheduleRelation(self, light_id = None, group_id = None, scene_id = None, schedule_id = None):
	#
	# 	sql = "DELETE FROM light_schedule_relation where 1=1 "
	#
	# 	params = []
	#
	# 	if light_id != None:
	# 		sql = sql + " and light_id = ? "
	# 		params.append(light_id)
	#
	# 	if group_id != None:
	# 		sql = sql + " and group_id = ? "
	# 		params.append(group_id)
	#
	# 	if scene_id != None:
	# 		sql = sql + " and scene_id = ? "
	# 		params.append(scene_id)
	#
	# 	if schedule_id != None:
	# 		sql = sql + " and schedule_id = ? "
	# 		params.append(schedule_id)
	#
	# 	self.conn.cursor().execute((sql), tuple(params))
	# 	self.conn.commit()

	# def countUsedScheduleIdByLightIdList(self, schedule_id, light_id_list):
	#
	# 	sql = ("select count(1) cnt from light_schedule_relation "
	# 			"where schedule_id = ? and light_id in ({seq})").format(seq = ','.join(['?']*len(light_id_list)))
	#
	# 	params = [schedule_id]
	# 	params.extend(light_id_list)
	#
	# 	data = self.conn.cursor().execute(sql, tuple(params))
	# 	return data.fetchall()[0][0]

	# def queryAllLightUsedScheduleList(self):
	# 	sql = "SELECT distinct light_id, schedule_id FROM light_schedule_relation order by light_id, schedule_id"
	# 	data = self.conn.cursor().execute(sql)
	#
	# 	colname = [ d[0] for d in data.description ]
	# 	return [ dict(zip(colname, r)) for r in data.fetchall() ]

	def getMaxSensor(self):
		data = self.conn.cursor().execute("SELECT * FROM sensors order by id desc ")
		
		colname = [ d[0] for d in data.description ]
		data_list = [ dict(zip(colname, r)) for r in data.fetchall() ]
		return data_list[0] if len(data_list) > 0 else None


	def getBeacons(self, uuid):
		sql = "SELECT * FROM beacons where uuid = ?"
		data = self.conn.cursor().execute(sql, (uuid,))
		
		colname = [ d[0] for d in data.description ]
		return [ dict(zip(colname, r)) for r in data.fetchall() ]


	def queryUseSceneScheduleIdList(self, scene_id):
		sql = "SELECT schedule_id FROM schedules where scene_id = ? "
		data = self.conn.cursor().execute(sql, (scene_id,))
		
		colname = [ d[0] for d in data.description ]
		return [ dict(zip(colname, r)) for r in data.fetchall() ]
	


def close_connection(exception):
	dataDao = DataDao.get_instance()
	dataDao.closeConnection()