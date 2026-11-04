MATCH (event:Event {id: "create_p-660979"})-[eventLink]-(object:Object)

RETURN DISTINCT
  event,
  eventLink,
  object
