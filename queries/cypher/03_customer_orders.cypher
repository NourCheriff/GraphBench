MATCH
  (customer:Customer {id: "Riviera Robotics SAS"})-[placesRel:PLACES]->
  (order:Order)
OPTIONAL MATCH (customer)--(placeEvent:Event {type: "place order"})--(order)
OPTIONAL MATCH (order)-[includesRel:INCLUDES]-(object:Object)
RETURN
  customer,
  placesRel,
  order,
  placeEvent.timestamp AS placedAt,
  includesRel,
  object
