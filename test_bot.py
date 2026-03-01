from AI_Backend.bot import bot

print('modes', bot.get_modes())
print('domains', bot.get_domains())
print('new conv', bot.create_new_conversation('user1'))
print('chat', bot.process_message('user1','hello'))
