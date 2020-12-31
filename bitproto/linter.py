"""
bitproto.linter
~~~~~~~~~~~~~~~

Built-in linter, skipable but not configurable.
"""

import abc
from dataclasses import dataclass
from typing import Callable, Optional, Tuple, TypeVar, Type as T, Generic, List

from bitproto._ast import (
    Alias,
    Constant,
    Definition,
    Enum,
    EnumField,
    Message,
    MessageField,
    Node,
    Proto,
)
from bitproto.errors import warning
from bitproto.errors import (
    Warning,
    EnumNameNotPascal,
    EnumHasNoFieldValue0,
    EnumFieldNameNotUpper,
    MessageNameNotPascal,
    MessageFieldNameNotSnake,
)

Result = Tuple[Optional[Warning], Optional[str]]

D = TypeVar("D", bound=Definition)

SUPPORTED_TYPES: Tuple[T[Definition], ...] = (
    Alias,
    Constant,
    Enum,
    EnumField,
    Message,
    MessageField,
    Proto,
)


class Rule(Generic[D]):
    """Abstract class to describe a lint rule."""

    @abc.abstractmethod
    def description(self) -> str:
        """Rule description."""
        raise NotImplementedError

    @abc.abstractmethod
    def target_class(self) -> T[D]:
        """Target ast class."""
        raise NotImplementedError

    @abc.abstractmethod
    def check(self, definition: D, name: Optional[str] = None) -> Result:
        """Checker function, returns warning and suggestion message.
        :param definition: The definition of typed D.
        :param name: The name this definition declared in its parent scope, if has.
        """
        raise NotImplementedError


class Linter:
    """The linter."""

    def filter_rules(self, target_class: T[D]) -> List[Rule[D]]:
        """Filter rule by target_class."""
        return [rule for rule in self.rules() if rule.target_class() is target_class]

    def run_rule_checker(
        self, rule: Rule[D], definition: D, name: Optional[str] = None
    ) -> None:
        """Run given rule's checker on given definition."""
        warning(*rule.check(definition, name=name))

    def lint(self, proto: Proto) -> None:
        """Run lint rules for definitions bound to this proto."""
        for definition_type in SUPPORTED_TYPES:
            items = proto.filter(definition_type, recursive=True, bound=proto)
            rules = self.filter_rules(definition_type)
            for name, definition in items:
                for rule in rules:
                    self.run_rule_checker(rule, definition, name=name)

    def rules(self) -> Tuple[Rule, ...]:
        """Rules collection.
        Subclasses could overload."""
        return (
            RuleEnumNamingPascal(),
            RuleEnumContains0(),
            RuleEnumFieldNamingUpper(),
            RuleMessageNamingPascal(),
            RuleMessageFieldNamingSnake(),
        )


def lint(proto: Proto) -> None:
    """Run default linter on given proto."""
    return Linter().lint(proto)


# Rule Implementations


class RuleEnumNamingPascal(Rule[Enum]):
    def description(self) -> str:
        return "Check if enum name is in pascal case."

    def target_class(self) -> T[Enum]:
        return Enum

    def check(self, definition: Enum, name: Optional[str] = None) -> Result:
        # TODO
        return EnumNameNotPascal.from_token(definition), "using abc"


class RuleEnumContains0(Rule[Enum]):
    def description(self) -> str:
        return "Check if enum contains a field 0."

    def target_class(self) -> T[Enum]:
        return Enum

    def check(self, definition: Enum, name: Optional[str] = None) -> Result:
        for field in definition.fields:
            if field.value == 0:
                return None, None
        return (
            EnumHasNoFieldValue0.from_token(definition),
            "define default enum value to 0",
        )


class RuleEnumFieldNamingUpper(Rule[EnumField]):
    def description(self) -> str:
        return "Check if enum field name is in upper case."

    def target_class(self) -> T[EnumField]:
        return EnumField

    def check(self, definition: EnumField, name: Optional[str] = None) -> Result:
        definition_name = name or definition.name
        if not definition_name.isupper():
            return EnumFieldNameNotUpper.from_token(definition), definition_name.upper()
        return None, None


class RuleMessageNamingPascal(Rule[Message]):
    def description(self) -> str:
        return "Check if message name is in pascal case."

    def target_class(self) -> T[Message]:
        return Message

    def check(self, definition: Message, name: Optional[str] = None) -> Result:
        # TODO
        return MessageNameNotPascal.from_token(definition), "using abc"


class RuleMessageFieldNamingSnake(Rule[MessageField]):
    def description(self) -> str:
        return "Check if message field name is in snake case."

    def target_class(self) -> T[MessageField]:
        return MessageField

    def check(self, definition: MessageField, name: Optional[str] = None) -> Result:
        # TODO
        return MessageFieldNameNotSnake.from_token(definition), "using abc"