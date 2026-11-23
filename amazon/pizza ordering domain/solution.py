from dataclasses import dataclass, replace
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import List, Mapping, Tuple


class PizzaSize(Enum):
    SMALL = 1
    MEDIUM = 2
    LARGE = 3

class PizzaCrust(Enum):
    CRUST_1 = 1
    CRUST_2 = 2

class Topping(Enum):
    TOPPING_1 = 1
    TOPPING_2 = 2
    TOPPING_3 = 3

class OrderState(Enum):
    SUBMITTED = 1
    PREPARING = 2
    READY = 3
    COMPLETED = 4
    CANCELLED = 5


class UnsupportedChoice(ValueError):
    pass


class EmptyOrder(ValueError):
    pass


class StaleQuote(ValueError):
    pass


class DuplicateSubmission(ValueError):
    pass


class InvalidTransition(ValueError):
    pass


@dataclass
class PizzaDraft:
    size: PizzaSize
    crust: PizzaCrust
    toppings: List[Topping]

    def build(self) -> "PizzaSpecification":
        return PizzaSpecification(self.size, self.crust, self.toppings)


@dataclass(frozen=True)
class PizzaSpecification:
    size: PizzaSize
    crust: PizzaCrust
    toppings: Tuple[Topping, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "toppings", tuple(self.toppings))


@dataclass(frozen=True)
class Cart:
    id: int
    version: int = 0
    pizzas: Tuple[PizzaSpecification, ...] = ()


@dataclass(frozen=True)
class PricedPizza:
    specification: PizzaSpecification
    price: int


@dataclass(frozen=True)
class Quote:
    cart_id: int
    cart_version: int
    pizzas: Tuple[PricedPizza, ...]
    subtotal: int
    tax: int
    total: int


@dataclass(frozen=True)
class Order:
    id: int
    cart_id: int
    pizzas: Tuple[PricedPizza, ...]
    subtotal: int
    tax: int
    total: int
    state: OrderState = OrderState.SUBMITTED


@dataclass(frozen=True)
class QuoteService:
    crust_prices: Mapping[PizzaCrust, int]
    size_ratio: Mapping[PizzaSize, int]
    topping_prices: Mapping[Topping, int]
    tax_rate: Decimal

    def __post_init__(self):
        for field, enum_type, minimum in (
            ("crust_prices", PizzaCrust, 0),
            ("size_ratio", PizzaSize, 1),
            ("topping_prices", Topping, 0),
        ):
            values = dict(getattr(self, field))
            if any(
                not isinstance(key, enum_type)
                or type(value) is not int
                or value < minimum
                for key, value in values.items()
            ):
                raise ValueError(f"Invalid {field}")
            object.__setattr__(self, field, MappingProxyType(values))
        if (
            not isinstance(self.tax_rate, Decimal)
            or not self.tax_rate.is_finite()
            or self.tax_rate < 0
        ):
            raise ValueError("tax_rate must be a nonnegative finite Decimal")

    def price_pizza(self, pizza: PizzaSpecification) -> PricedPizza:
        """Only choices present in the configured mappings are active."""
        if (
            not isinstance(pizza.size, PizzaSize)
            or pizza.size not in self.size_ratio
            or not isinstance(pizza.crust, PizzaCrust)
            or pizza.crust not in self.crust_prices
            or any(
                not isinstance(topping, Topping)
                or topping not in self.topping_prices
                for topping in pizza.toppings
            )
        ):
            raise UnsupportedChoice("Pizza contains an inactive or unknown choice")
        base = self.crust_prices[pizza.crust] + sum(
            self.topping_prices[topping] for topping in pizza.toppings
        )
        return PricedPizza(pizza, base * self.size_ratio[pizza.size])

    def calculate_quote(self, cart: Cart) -> Quote:
        if not cart.pizzas:
            raise EmptyOrder("Cannot quote an empty cart")
        pizzas = tuple(self.price_pizza(pizza) for pizza in cart.pizzas)
        subtotal = sum(pizza.price for pizza in pizzas)
        # Exact integer arithmetic gives half-up rounding without Decimal context limits.
        numerator, denominator = self.tax_rate.as_integer_ratio()
        tax = (2 * subtotal * numerator + denominator) // (2 * denominator)
        return Quote(cart.id, cart.version, pizzas, subtotal, tax, subtotal + tax)


class PizzaSystem:
    def __init__(self, quote_service: QuoteService):
        self.quote_service = quote_service
        self._carts: dict[int, Cart] = {}
        self._quotes: dict[int, Quote] = {}
        self._orders: dict[int, Order] = {}
        self._submitted: dict[int, int] = {}

    def create_cart(self) -> Cart:
        cart = Cart(id=len(self._carts) + 1)
        self._carts[cart.id] = cart
        return cart

    def get_cart(self, cart_id: int) -> Cart:
        return self._carts[cart_id]

    def _editable_cart(self, cart_id: int) -> Cart:
        cart = self.get_cart(cart_id)
        if cart_id in self._submitted:
            raise DuplicateSubmission("Cart has already been submitted")
        return cart

    def add_pizza(self, cart_id: int, pizza: PizzaSpecification) -> Cart:
        cart = self._editable_cart(cart_id)
        self.quote_service.price_pizza(pizza)
        updated = replace(
            cart, version=cart.version + 1, pizzas=cart.pizzas + (pizza,)
        )
        self._carts[cart_id] = updated
        return updated

    def remove_pizza(self, cart_id: int, index: int) -> Cart:
        cart = self._editable_cart(cart_id)
        if not 0 <= index < len(cart.pizzas):
            raise IndexError("Pizza index is out of range")
        updated = replace(
            cart,
            version=cart.version + 1,
            pizzas=cart.pizzas[:index] + cart.pizzas[index + 1:],
        )
        self._carts[cart_id] = updated
        return updated

    def quote_cart(self, cart_id: int) -> Quote:
        cart = self._editable_cart(cart_id)
        quote = self.quote_service.calculate_quote(cart)
        self._quotes[cart_id] = quote
        return quote

    def submit_cart(self, cart_id: int, quote: Quote) -> Order:
        cart = self._editable_cart(cart_id)
        if not cart.pizzas:
            raise EmptyOrder("Cannot submit an empty cart")
        if (
            quote.cart_id != cart_id
            or quote.cart_version != cart.version
            or self._quotes.get(cart_id) != quote
        ):
            raise StaleQuote("Request a new quote for the current cart")
        try:
            current_quote = self.quote_service.calculate_quote(cart)
        except UnsupportedChoice as error:
            raise StaleQuote("Quoted menu choices are no longer active") from error
        if current_quote != quote:
            raise StaleQuote("Menu prices or tax have changed; request a new quote")
        order = Order(
            id=len(self._orders) + 1,
            cart_id=cart_id,
            pizzas=quote.pizzas,
            subtotal=quote.subtotal,
            tax=quote.tax,
            total=quote.total,
        )
        self._orders[order.id] = order
        self._submitted[cart_id] = order.id
        return order

    def get_order(self, order_id: int) -> Order:
        return self._orders[order_id]

    def transition_order(self, order_id: int, target: OrderState) -> Order:
        order = self.get_order(order_id)
        allowed = {
            OrderState.SUBMITTED: (OrderState.PREPARING, OrderState.CANCELLED),
            OrderState.PREPARING: (OrderState.READY,),
            OrderState.READY: (OrderState.COMPLETED,),
        }
        if target not in allowed.get(order.state, ()):
            raise InvalidTransition(
                f"Cannot move from {order.state.name} to {target!r}"
            )
        updated = replace(order, state=target)
        self._orders[order_id] = updated
        return updated
