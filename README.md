# GraphBench

Comparative study of RDF triplestore and graph approaches for modeling and querying large OCEL datasets, with a focus on expressiveness and performance.

## Table of Contents

1. [Dataset](#dataset)
2. [Analysis](#analysis)
   1. [Event Types](#event-types)
   2. [Object Types](#object-types)
   3. [Object Relationships](#object-relationships)
3. [Knowledge Graph Model](#knowledge-graph-model)
   1. [Neo4j](#neo4j)
   2. [GraphDB](#graphdb)
4. [Benchmarking](#benchmarking)

---


# Dataset

This project uses the **Order Management** event log from the [OCEL 2.0 event-log collection](https://www.ocel-standard.org/event-logs/simulations/order-management/).

The dataset represents an order management process involving customers, orders, items, products, packages, and employees.

| Property | Value |
|---|---:|
| Event Types | 11 |
| Object Types | 6 |
| Events | 21,008 |
| Objects | 10,840 |

# Analysis

## Event Types

The dataset contains the following event types:

| Event Type | Attributes |
|---|---|
| `pay order` | `[]` |
| `package delivered` | `[]` |
| `place order` | `[]` |
| `create package` | `[]` |
| `confirm order` | `[]` |
| `item out of stock` | `[]` |
| `pick item` | `[]` |
| `send package` | `[]` |
| `payment reminder` | `[]` |
| `reorder item` | `[]` |
| `failed delivery` | `[]` |

Event instances contain additional information such as:

| Information | Purpose |
|---|---|
| `id` | Identifier of the instance |
| `type` | Type of instance |
| `time` | Timestamp in ISO-8601 format |
| `relationships` | Array of related objects to the event, each `relationship` has the `objectId` and the `qualifier` |

> [!IMPORTANT]
> In our case, event instances hasn't additional attributes than `type` and `time`


## Object Types

The dataset contains the following object types:

| Object Type | Attributes |
|---|---|
| `orders` | `price: float` |
| `items` | `weight: float`, `price: float` |
| `packages` | `weight: float` |
| `customers` | None |
| `products` | `weight: float`, `price: float` |
| `employees` | `role: string` |

## Object Relationships

The following **relationships** are identified from the **Order Management** dataset and its process description.

| Source Object | Relationship | Target Object | Source |
|---|---|---|---|
| `customers` | `places` | `orders` | Domain semantics |
| `orders` | `contains` | `items` | Domain semantics |
| `items` | `represents` | `products` | Domain semantics |
| `orders` | `assignedTo` | `employees` | Domain semantics |
| `employees` | `primarySalesRep` | `customers` | Dataset |
| `employees` | `secondarySalesRep` | `customers` | Dataset |
| `employees` | `checksAvailabilityOf` | `items` | Domain semantics |
| `employees` | `reorders` | `items` | Domain semantics |
| `items` | `pickedInto` | `packages` | Domain semantics |
| `orders` | `distributedOver` | `packages` | Domain semantics |
| `packages` | `addressedTo` | `customers` | Domain semantics |
| `packages` | `packedBy` | `employees` | Dataset |
| `packages` | `forwardedBy` | `employees` | Dataset |
| `packages` | `shippedBy` | `employees` | Dataset |
| `packages` | `deliveredTo` | `customers` | Domain semantics |

> [!NOTE]
> `Dataset` indicates that the relationship is explicitly defined in the dataset, while `Domain semantics` indicates that the relationship is derived from the process description. The distinction will be considered when constructing the conceptual model.
