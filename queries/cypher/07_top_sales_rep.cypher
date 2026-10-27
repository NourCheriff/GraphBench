MATCH (employee:Employee)--(confirmEvent:Event {type: "confirm order"})
RETURN employee, count(DISTINCT confirmEvent) AS confirmedOrders
ORDER BY confirmedOrders, employee.id DESC
LIMIT 1
