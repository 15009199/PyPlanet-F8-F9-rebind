import json

from pyplanet.apps.core.pyplanet.models.setting import Setting as SettingModel
from pyplanet.contrib.setting.exceptions import TypeUnknownException, SerializationException, SettingException


class Setting:
	"""
	The setting class is for defining a setting for the end-user. 
	This setting can be changed with /settings and //settings.
	
	.. todo::
	
		Provide examples.
	
	"""

	CAT_GENERAL = 'General'
	CAT_DESIGN = 'Design'
	CAT_POSITION = 'Position'
	CAT_BEHAVIOUR = 'Behaviour'
	CAT_FEATURES = 'Features'
	CAT_OTHER = 'Other'
	ALL_CATEGORIES = [CAT_GENERAL, CAT_DESIGN, CAT_POSITION, CAT_BEHAVIOUR, CAT_FEATURES, CAT_OTHER]

	def __init__(
		self, key: str, name: str, category: str, type=str, description: str = None, choices=None, default=None,
	):
		"""
		Create setting with properties.
		
		:param key: Key of setting, this is mainly only used for the backend and for referencing the setting. 
					You should keep this unique in your app!
		:param name: Name of the setting that will be displayed as a small label to the player.
		:param category: Category from Categories.*. Must be provided!
		:param type: Type of value to expect, use python types here. str by default.
		:param description: Description to provide help and instructions to the player.
		:param choices: List or tuple with choices, only when wanting to restrict values to selected options.
		:param default: Default value if not provided from database. This will be returned. Defaults to None.
		"""
		if category not in self.ALL_CATEGORIES:
			raise SettingException('Invalid category. Must be an category in the Categories static class.')
		# Prepare property for app specific setting. Will be injected by the register command.
		self.app_label = None

		self.key = key
		self.name = name
		self.description = description
		self.category = category
		self.default = default
		self.type = type
		self.choices = choices # TODO.

		# Prepare the model instance here. This will be filled once it's fetched for the first time (or inited).
		self._instance = None
		self._value = (False, None)

	async def initiate_setting(self):
		"""
		Initiate database record for setting.
		"""
		return await SettingModel.get_or_create_from_info(
			key=self.key, app=self.app_label, category=self.category, name=self.name, description=self.description,
			value=None
		)

	def unserialize_value(self, value):
		"""
		Unserialize the datastorage value to the python value, based on the type of the setting.
		
		:param value: Value from database.
		:return: Python value.
		:raise pyplanet.contrib.setting.exceptions.SerializationException: SerializationException
		"""
		if value is None:
			return self.default

		try:
			if self.type == str:
				return str(value)
			elif self.type == int:
				return int(value)
			elif self.type == float:
				return float(value)
			elif self.type == bool:
				return bool(value)
			elif self.type == list or self.type == set or self.type == dict:
				return json.loads(value)
			else:
				raise TypeUnknownException('The type \'{}\' is unknown!'.format(self.type))
		except TypeUnknownException:
			raise
		except Exception as e:
			raise SerializationException('Error with unserialization of the setting \'{}\''.format(str(self))) from e

	def serialize_value(self, value):
		"""
		Serialize the python value to the data store value, based on the type of the setting.

		:param value: Python Value.
		:return: Database Value
		"""
		# Always set to Null, so we get the default value back.
		if value is None:
			return value

		if self.choices and value not in self.choices:
			raise SerializationException('Value given is not in the predefined choices!')

		try:
			if self.type == int:
				value = int(value)
			elif self.type == float:
				value = float(value)
			elif self.type == bool:
				if value == '1' or value == 1 or value == '0' or value == 0:
					value = bool(value)
		except:
			pass

		if type(value) != self.type:
			raise SerializationException(
				'Your given value is not of the type you specified! \'{}\' != \'{}\''.format(type(value), self.type)
			)

		if self.type == list or self.type == set or self.type == dict:
			return json.dumps(value)
		return value

	@property
	def type_name(self):
		"""
		Get the name of the specified type in string format, suited for displaying to end-user.
		
		:return: User friendly name of type.
		"""
		if self.type == str:
			return 'string'
		elif self.type == int:
			return 'integer'
		elif self.type == float:
			return 'float'
		elif self.type == bool:
			return 'boolean'
		elif self.type == list or self.type == set or self.type == dict:
			return 'list/dict'
		else:
			return 'unknown'

	async def get_value(self, refresh=False):
		"""
		Get the value or the default value for the setting model.

		:param refresh: Force a refresh of the value.
		:return: Value in the desired type and unserialized from database/storage.
		:raise: NotFound / SerializationException
		"""
		if not self._value[0] or refresh is True:
			model = await self.get_model()
			self._value = (True, self.unserialize_value(model.value))
		return self._value[1]

	async def set_value(self, value):
		"""
		Set the value, this will serialize and save the setting to the data storage.
		
		:param value: Python value input.
		:raise: NotFound / SerializationException
		"""
		model = await self.get_model()
		model.value = self.serialize_value(value)
		self._value = (True, model.value)
		await model.save()

	async def clear(self):
		"""
		Clear the value in the data storage. This will set the value to None, and will return the default value on
		request of data. 
		
		:raise: NotFound / SerializationException
		"""
		return await self.set_value(None)

	async def get_model(self):
		"""
		Get the model for the setting. This will return the model instance or raise an exception when not found.
		
		:return: Model instance
		:raise: NotFound
		"""
		return await SettingModel.get(key=self.key, app=self.app_label)

	def __str__(self):
		return self.name
