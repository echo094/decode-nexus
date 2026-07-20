# MovedDeclarations

Source: `transforms/identifier/movedDeclarations.ts`

Hoists single-declarator `var` statements either to the top of their block or (when
eligible) into the enclosing function's parameter list with a default value; also
converts named function declarations into `if(!name) name = function(){...}` guards.

## Reversal

Mostly cosmetic reordering — doesn't need undoing for comprehension, though recognizing
the pattern helps avoid confusion when reading parameter lists.
