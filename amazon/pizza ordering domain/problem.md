Model customizable pizzas, cart pricing, order submission, and guarded kitchen-state transitions.

Problem statement
Design the low-level object model and contracts for a pizza ordering application. For this exercise, assume a customer builds one or more pizzas by choosing a size, crust, and toppings from an active menu; receives a deterministic quote that adds sales tax; and submits the cart as one order.

Tax uses one configured rate on the cart's pizza subtotal after any price adjustments; all amounts are whole cents, and tax is computed once per quote and rounded half up to the nearest cent. A submitted order snapshots every pizza specification and price and the quoted tax.

Kitchen staff may move it from submitted to preparing, ready, and completed, while cancellation is allowed only before preparation begins. Unsupported choices, empty orders, stale quotes, duplicate submissions, and invalid state transitions must have explicit outcomes.

Menu storage, payment execution, delivery routing, and user-interface details are outside scope.