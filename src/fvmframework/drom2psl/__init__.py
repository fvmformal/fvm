"""
Convert .json wavedrom files to .psl sequences

In order for this to be usable, we are assuming a number of things in the
input .json files:

1. That the clock is the first signal that appears in the wavedrom
2. That only the clock carries the repeat zero-or-more symbol '|'
3. That the user has defined the datatype of any 'data' in a 'type' field in
   the wavelane, for example:

   .. code-block:: json

      {name: 'dat', wave: 'x.3x', data: 'data', type: 'std_ulogic_vector(31 downto 0)'},

4. That, if we have two top-level groups, then we are describing some relation
   between two sequences and thus a sample property will be generated in the
   PSL file relating the two sequences
"""
