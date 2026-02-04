# Macro syntax

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

### Error handling

- Anything in `{ }` in a template is variable.
- Error if not defaulted and not defined.
- Otherwise, just text substitution.

---

## Multi-line templates (implemented)

**Define:**
- @>contrib_tufts name dept  (params, no defaults)
- @>contrib_tufts name={Alva Couch} dept={Engineering}  (with defaults)
- Body: >@contributor {name}, >@contributor-institution Tufts University, etc.
- Macro ends when there’s no >.

**Invoke:**
- @<contrib_tufts  (use defaults if all params have defaults)
- @<contrib_tufts name={Alva Couch} dept={Computer Science}  (explicit args)

**Error:** If {var} in template has no default and is not provided at invocation.
