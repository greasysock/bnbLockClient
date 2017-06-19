from support import zwayapi

zway = zwayapi.Connect(0)

zway.get_locations()
zway.get_status()