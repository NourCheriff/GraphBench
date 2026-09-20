# GraphBench

Comparative study of RDF triplestore and graph approaches for modeling and querying large OCEL datasets, with a focus on expressiveness and performance.

## Table of Contents

1. [Background: OCEL 2.0](#background-ocel-20)
2. [Dataset](#dataset)
   1. [Physical Schema (SQLite)](#physical-schema-sqlite)
3. [Analysis](#analysis)
   1. [Event Types](#event-types)
   2. [Object Types](#object-types)
   3. [Event-to-Object Relationships (E2O)](#event-to-object-relationships-e2o)
   4. [Object-to-Object Relationships (O2O)](#object-to-object-relationships-o2o)
   5. [Domain Considerations](#domain-considerations)
4. [Knowledge Graph Model](#knowledge-graph-model)
   1. [Neo4j](#neo4j)
   2. [GraphDB](#graphdb)
5. [Benchmarking](#benchmarking)

---

# Background: OCEL 2.0

**OCEL** stands for **Object-Centric Event Log**. Unlike traditional event logs, which associate each event with a single case, an object-centric log allows an event to be linked to many objects of different types, and an object to participate in many events.

![OCEL 2.0 metamodel](docs/img/ocel20-metamodel.png)

_Source: [OCEL 2.0 Specification](https://www.ocel-standard.org/specification/overview)_

Key elements of the metamodel:

| Element | Description                                                                                                                                  |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Event   | Has exactly one type (activity) and one timestamp. Its attributes are **static**: their values are fixed when the event occurs.              |
| Object  | Has exactly one type. Its attributes are **dynamic**: each value is linked to the timestamp at which it was set, so it can change over time. |
| E2O     | Event-to-Object relationship (many-to-many), optionally labeled with a **qualifier**.                                                        |
| O2O     | Object-to-Object relationship (many-to-many), optionally labeled with a **qualifier**. In the metamodel it has **no timestamp**.             |

The metamodel is organized on two levels: the **type level** (event types, object types and their declared attributes) and the **instance level** (events, objects and attribute values).

# Dataset

This project uses the **Order Management** event log from the [OCEL 2.0 event-log collection](https://www.ocel-standard.org/event-logs/simulations/order-management/).

The dataset describes the management of customer orders within a company: registration and payment of incoming orders, and packing and shipping of the ordered items. The company employs staff in the sales, warehousing and shipment departments.

| Property     |  Value |
| ------------ | -----: |
| Event Types  |     11 |
| Object Types |      6 |
| Events       | 21,008 |
| Objects      | 10,840 |

## Physical Schema (SQLite)

The dataset is distributed as an SQLite database following the OCEL 2.0 relational schema.

![SQLite schema](docs/img/sqlite-schema.png)

| Table                      | Content                                                  | Metamodel element                                                |
| -------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------- |
| `event`                    | `ocel_id`, `ocel_type`                                   | Event, _has type_                                                |
| `event_map_type`           | `ocel_type`, `ocel_type_map`                             | Event type → name of its per-type table                          |
| `event_<Type>` (11 tables) | `ocel_id`, `ocel_time`                                   | _has timestamp_ (+ event attribute values, none in this dataset) |
| `object`                   | `ocel_id`, `ocel_type`                                   | Object, _has type_                                               |
| `object_map_type`          | `ocel_type`, `ocel_type_map`                             | Object type → name of its per-type table                         |
| `object_<Type>` (6 tables) | `ocel_id`, `ocel_time`, `ocel_changed_field`, attributes | Object attribute values with their timestamp                     |
| `event_object`             | `ocel_event_id`, `ocel_object_id`, `ocel_qualifier`      | E2O (_has objects_ + qualifier)                                  |
| `object_object`            | `ocel_source_id`, `ocel_target_id`, `ocel_qualifier`     | O2O (_related_ + qualifier)                                      |

> Attribute changes are stored as **additional rows** in the `object_<Type>` tables: `ocel_time` is the moment the value was set and `ocel_changed_field` names the attribute that changed. The `object_object` table has no time column, consistent with the metamodel.

# Analysis

## Event Types

Events are grouped by the department that performs them.

| Area      | Event Type          |
| --------- | ------------------- |
| Sales     | `place order`       |
| Sales     | `confirm order`     |
| Sales     | `payment reminder`  |
| Sales     | `pay order`         |
| Warehouse | `item out of stock` |
| Warehouse | `reorder item`      |
| Warehouse | `pick item`         |
| Warehouse | `create package`    |
| Shipment  | `send package`      |
| Shipment  | `failed delivery`   |
| Shipment  | `package delivered` |

> In this dataset, events have no attributes other than their `type` and `time`. All the information about an event is carried by its E2O relationships.

## Object Types

| Object Type | Attributes                      |
| ----------- | ------------------------------- |
| `orders`    | `price: float`                  |
| `items`     | `weight: float`, `price: float` |
| `packages`  | `weight: float`                 |
| `customers` | –                               |
| `products`  | `weight: float`, `price: float` |
| `employees` | `role: string`                  |

## Event-to-Object Relationships (E2O)

For each event type, the object types it is linked to and the qualifiers used.

## Object-to-Object Relationships (O2O)

Relationships are split by **how they are obtained**, because this affects the conceptual model.

### Explicit in the dataset (`object_object` table)

| Source Object | Qualifier           | Target Object |
| ------------- | ------------------- | ------------- |
| `employees`   | `primarySalesRep`   | `customers`   |
| `employees`   | `secondarySalesRep` | `customers`   |
| `packages`    | `packed by`         | `employees`   |
| `packages`    | `forwarded by`      | `employees`   |
| `packages`    | `shipped by`        | `employees`   |

> The dataset documentation lists the relationships above "among others": the full list must be extracted from the `object_object` table. Qualifier spelling must match the data.

## Domain Considerations

- **Many-to-many between orders and packages.** A package can contain items of several orders, and an order can be distributed over several packages.
- **Dynamic attributes.** Product prices increase irregularly due to inflation, which reduces customers' order volumes.
- **Single-face-to-customer policy.** Each customer has a primary sales representative; if unavailable, a secondary one takes over; otherwise any other employee.
- **Loading policy.** A warehousing employee should help the shipment employee load a package, but shippers often load alone or with a second shipment employee.
- **Repeated activities.** Deliveries can fail several times before succeeding.

# Knowledge Graph Model

## Neo4j

TBD (WP4)

## GraphDB

TBD (WP3)

# Benchmarking

TBD (WP7, WP8, WP11)
