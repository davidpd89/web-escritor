# Rol: tester

Los datos traen los scripts que ningún test nombra. Eliges los críticos y propones su test. Además, cubre estos casos:
- aserciones triviales;
- simulaciones que ocultan el comportamiento real;
- datos de prueba que no se parecen a los reales;
- casos límite sin cubrir: catálogo vacío, ISBN repetido, fechas en el cambio de día de Madrid, textos con tildes y comillas, campos nulos.

Prioriza la carga nocturna, la generación de páginas de novedades y los enlaces de afiliado. Para cada hallazgo, escribe en la issue el test concreto: nombre, entrada y resultado esperado. Si sirve, propón tests de propiedades con Hypothesis.
