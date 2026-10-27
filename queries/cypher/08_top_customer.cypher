MATCH (customer:Customer)-[:PLACES]->(order:Order)
RETURN customer, count(order) AS ordersPlaced, sum(order.price) AS totalSpent
ORDER BY ordersPlaced DESC
LIMIT 1
