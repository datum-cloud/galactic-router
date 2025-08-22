@wip
Feature: Endpoint leaves established VPC
We emit route deletions for the endpoint to the remaining workers.

Scenario: First endpoint joins VPC
When a register event is received from "node1" for network "10.1.1.1/32" and endpoint "2001::1"
Then 0 routes were published

Scenario: Second endpoint joins VPC
When a register event is received from "node2" for network "10.1.1.2/32" and endpoint "2001::2"
Then 2 routes were published

Scenario: First endpoint leaves VPC
When a deregister event is received from "node1" for network "10.1.1.1/32" and endpoint "2001::1"
Then 1 route was published
And the route is as follows:
| worker | network     | endpoint | segments | status |
| node2  | 10.1.1.1/32 | 2001::2  | 2001::1  | DELETE |
