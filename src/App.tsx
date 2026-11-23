/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * Componente raíz mínimo ("Hello World") requerido únicamente para que
 * el entorno web de Vite/React compile correctamente mientras el proyecto
 * principal del juego móvil reside configurado en la carpeta /godot.
 */
export default function App() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-neutral-950 text-neutral-100">
      <h1 className="text-2xl font-mono tracking-wide">Hello World</h1>
    </main>
  );
}
