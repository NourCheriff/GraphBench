MATCH (order:Order)
WITH count(order) AS totalOrders

MATCH (order:Order)-[:INCLUDES]->(:Item)<-[:CONTAINS]-(package:Package)
WITH totalOrders, order, COUNT(DISTINCT package) AS packageCount
WHERE packageCount > 1

RETURN
  count(order) AS splitOrders,
  totalOrders,
  toFloat(count(order)) / totalOrders AS splitRatio
