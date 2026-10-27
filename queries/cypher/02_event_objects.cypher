MATCH (event:Event {id: "create_p-660979"})-[eventLink]-(object:Object)
OPTIONAL MATCH (event)-[otherEventLink]-(otherObject:Object)
WHERE otherObject <> object

OPTIONAL MATCH (object)-[objectLink]-(otherObject)

RETURN DISTINCT
  event,
  eventLink,
  object,
  otherEventLink,
  otherObject,
  objectLink
