@wip
Feature: VPC setup between endpoints
We emit route additions for the relevant endpoints to the workers.

Scenario: First endpoint joins VPC
When a register event is received from "node1" for network "10.1.1.1/32" and endpoint "2001::1"
Then 0 routes were published

Scenario: Second endpoint joins VPC
When a register event is received from "node2" for network "10.1.1.2/32" and endpoint "2001::2"
Then 2 routes were published
And the routes are as follows:
| worker | network     | endpoint | segments | status |
| node1  | 10.1.1.2/32 | 2001::1  | 2001::2  | ADD    |
| node2  | 10.1.1.1/32 | 2001::2  | 2001::1  | ADD    |

Scenario: Third endpoint joins VPC
When a register event is received from "node3" for network "10.1.1.3/32" and endpoint "2001::3"
Then 4 routes were published
And the routes are as follows:
| worker | network     | endpoint | segments | status |
| node1  | 10.1.1.3/32 | 2001::1  | 2001::3  | ADD    |
| node2  | 10.1.1.3/32 | 2001::2  | 2001::3  | ADD    |
| node3  | 10.1.1.1/32 | 2001::3  | 2001::1  | ADD    |
| node3  | 10.1.1.2/32 | 2001::3  | 2001::2  | ADD    |
