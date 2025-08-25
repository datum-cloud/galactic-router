@wip
Feature: Endpoint moves from one worker to another
We emit route additions and deletions for the relevant endpoints to the workers.

Scenario: First endpoint joins VPC
When a register event is received from "node1" for network "10.1.1.1/32" and endpoint "2001:1::1234:1234:1234:ffff"
Then 1 routes were published
| worker | network     | endpoint                    | segments                    | status |
| node1  | 10.1.1.1/32 | 2001:1::1234:1234:1234:ffff | 2001:1::1234:1234:1234:ffff | ADD    |

Scenario: Second endpoint joins VPC
When a register event is received from "node2" for network "10.1.1.2/32" and endpoint "2001:2::1234:1234:1234:ffff"
Then 3 routes were published
And the routes are as follows:
| worker | network     | endpoint                    | segments                    | status |
| node1  | 10.1.1.2/32 | 2001:1::1234:1234:1234:ffff | 2001:2::1234:1234:1234:ffff | ADD    |
| node2  | 10.1.1.2/32 | 2001:2::1234:1234:1234:ffff | 2001:2::1234:1234:1234:ffff | ADD    |
| node2  | 10.1.1.1/32 | 2001:2::1234:1234:1234:ffff | 2001:1::1234:1234:1234:ffff | ADD    |

Scenario: First endpoint moves to another worker
When a register event is received from "node3" for network "10.1.1.1/32" and endpoint "2001:3::1234:1234:1234:ffff"
Then 5 routes were published
And the routes are as follows:
| worker | network     | endpoint                    | segments                    | status |
| node1  | 10.1.1.1/32 | 2001:1::1234:1234:1234:ffff | 2001:1::1234:1234:1234:ffff | DELETE |
| node2  | 10.1.1.1/32 | 2001:2::1234:1234:1234:ffff | 2001:1::1234:1234:1234:ffff | DELETE |
| node2  | 10.1.1.1/32 | 2001:2::1234:1234:1234:ffff | 2001:3::1234:1234:1234:ffff | ADD    |
| node3  | 10.1.1.1/32 | 2001:3::1234:1234:1234:ffff | 2001:3::1234:1234:1234:ffff | ADD    |
| node3  | 10.1.1.2/32 | 2001:3::1234:1234:1234:ffff | 2001:2::1234:1234:1234:ffff | ADD    |
