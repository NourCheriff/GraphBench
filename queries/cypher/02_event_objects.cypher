MATCH (event:Event {id: $event})-[eventLink]-(object:Object)

RETURN DISTINCT
  event,
  eventLink,
  object
