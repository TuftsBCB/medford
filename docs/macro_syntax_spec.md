# Macro syntax — exact spec (as given)

## Simple variables (in-file, implemented)

### Defining a variable

`@name Value

– or –

`@name {A value} # if spaces in value

- **Name:** Letters, digits, underscore; must start with a letter.
- **Value (unbraced):** Rest of line. `#` starts an inline comment (stripped).
- **Value (braced):** `{...}` with brace matching. Inner braces stay in the value.

**Chaos example:** If you write

`@name {chaos {reigns}}

then

`name

expands to

chaos {reigns}

### Expanding

`name or `{name} # optional

- **Use** = `` `name `` or `` `{name} ``. No `@` in use; definition uses `` `@ ``.
- Braces around the name are optional.

### Error handling (from spec)

- Anything in `{ }` in a template is variable.
- Error if not defaulted and not defined.
- Otherwise, just text substitution.

---

## Multi-line templates (not yet implemented)

**Define:** @>contrib_tufts name dept  (params optional), then >@… body lines. Macro ends when there’s no >.

**Invoke:** @<contrib_tufts  or  @<contrib_tufts name={Alva Couch} dept={Computer Science}

**With defaults:** @<contrib_tufts  expands the same as when args given.
