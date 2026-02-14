
+  const poolConfig = {
+    max: 20,
+    min: 5,
+    idleTimeoutMillis: 30000,
+    connectionTimeoutMillis: 2000
+  };
+  const pool = new Pool(poolConfig);
