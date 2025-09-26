#!/usr/bin/env node

// Debug script to check file structure and module resolution
const fs = require('fs');
const path = require('path');

console.log('=== VERCEL BUILD DEBUG ===');
console.log('Current working directory:', process.cwd());
console.log('Node version:', process.version);
console.log('NODE_ENV:', process.env.NODE_ENV);

// Check if lib directory exists
const libPath = path.join(process.cwd(), 'lib');
console.log('\n=== LIB DIRECTORY CHECK ===');
console.log('lib directory exists:', fs.existsSync(libPath));
if (fs.existsSync(libPath)) {
  console.log('lib directory contents:', fs.readdirSync(libPath));
  
  // Check if utils.ts exists
  const utilsPath = path.join(libPath, 'utils.ts');
  console.log('utils.ts exists:', fs.existsSync(utilsPath));
  if (fs.existsSync(utilsPath)) {
    console.log('utils.ts content preview:', fs.readFileSync(utilsPath, 'utf8').substring(0, 100));
  }
}

// Check components directory
const componentsPath = path.join(process.cwd(), 'components');
console.log('\n=== COMPONENTS DIRECTORY CHECK ===');
console.log('components directory exists:', fs.existsSync(componentsPath));
if (fs.existsSync(componentsPath)) {
  console.log('components directory contents:', fs.readdirSync(componentsPath));
  
  const uiPath = path.join(componentsPath, 'ui');
  console.log('components/ui directory exists:', fs.existsSync(uiPath));
  if (fs.existsSync(uiPath)) {
    console.log('components/ui directory contents:', fs.readdirSync(uiPath));
  }
}

// Check tsconfig.json
const tsconfigPath = path.join(process.cwd(), 'tsconfig.json');
console.log('\n=== TSCONFIG CHECK ===');
console.log('tsconfig.json exists:', fs.existsSync(tsconfigPath));
if (fs.existsSync(tsconfigPath)) {
  const tsconfig = JSON.parse(fs.readFileSync(tsconfigPath, 'utf8'));
  console.log('tsconfig paths:', tsconfig.compilerOptions?.paths);
}

// Check jsconfig.json
const jsconfigPath = path.join(process.cwd(), 'jsconfig.json');
console.log('\n=== JSCONFIG CHECK ===');
console.log('jsconfig.json exists:', fs.existsSync(jsconfigPath));
if (fs.existsSync(jsconfigPath)) {
  const jsconfig = JSON.parse(fs.readFileSync(jsconfigPath, 'utf8'));
  console.log('jsconfig paths:', jsconfig.compilerOptions?.paths);
}

// Check next.config.ts
const nextConfigPath = path.join(process.cwd(), 'next.config.ts');
console.log('\n=== NEXT CONFIG CHECK ===');
console.log('next.config.ts exists:', fs.existsSync(nextConfigPath));

console.log('\n=== DEBUG COMPLETE ===');
