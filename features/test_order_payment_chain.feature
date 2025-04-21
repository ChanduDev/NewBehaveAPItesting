@regression
Feature: Chained workflow from Cart to Order to Payment

  Background:
    Given I use the "cart" env config
    And I load test data from "workflow_test_data.csv"
    And I fetch MongoDB data from query

  Scenario: Create Cart
    When I select row 0 to load the API contract details
    And I override values using mappings
      | headers.Authorization | access_token |
    And I send a POST request to "/cart" with API contract details
    Then the response status code should be 201
    And I save response values using mappings
      | body.cart.id | cartId |

  Scenario: Create Order using Cart ID
    Given I use the "cart" env config
    When I select row 1 to load the API contract details
    And I override values using mappings
      | headers.Authorization | access_token |  
      | body.order.cart_id    | cartId       |
    And I send a POST request to "/order" with API contract details
    Then the response status code should be 201
    And I save response values using mappings
      | body.order.id | orderId |

  Scenario: Pay for Order using Order ID
    Given I use the "cart" env config
    When I select row 2 to load the API contract details
    And I override values using mappings
      | headers.Authorization | access_token |
      | body.payment.order_id | orderId      |
    And I send a POST request to "/pay/{orderId}" with API contract details
    Then the response status code should be 200
    And I validate response values using mappings
      | body.payment.status | success |