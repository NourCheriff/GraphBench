MATCH (employee:Employee)<-[:SHIPPED_BY]-(package:Package)
RETURN employee, count(package) AS shippedPackages
ORDER BY shippedPackages DESC
LIMIT 3
