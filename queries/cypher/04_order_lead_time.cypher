MATCH
  (placeEvent:Event {type: "place order"})--
  (order:Order)-[:INCLUDES]->
  (:Item)<-[:CONTAINS]-
  (package:Package)
MATCH (deliveredEvent:Event {type: "package delivered"})--(package)
WITH order, placeEvent, max(deliveredEvent.timestamp) AS lastDeliveredTime

RETURN
  order.id AS orderId,
  duration.inSeconds(placeEvent.timestamp, lastDeliveredTime).hours AS deliveryHours
ORDER BY deliveryHours DESC
