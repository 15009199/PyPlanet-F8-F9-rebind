from pyplanet.views import TemplateView


class ControllerView(TemplateView):
	template_name = 'core.pyplanet/controller.xml'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.id = 'pyplanet__controller'

		self.subscribe('f10', self.action_f10)

	async def get_context_data(self):
		from pyplanet.core import Controller
		context = await super().get_context_data()
		context['game'] = Controller.instance.game.game

		context['chat_pos'] = '-160.25 -63.75'
		if context['game'] != 'tm':
			context['chat_pos'] = '-160.25 -39.75'

		return context

	async def display(self, **kwargs):
		return await super().display(**kwargs)

	async def action_f10(self, player, *args, **kwargs):
		await self.manager.instance.chat(
			'$ff0Toggling visibility. You can show/hide with f10, and show/hide when driving with f11', player
		)
