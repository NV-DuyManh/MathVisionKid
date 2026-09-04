const fs = require('fs');

function fixFontWeight(file) {
  if (!fs.existsSync(file)) return;
  let content = fs.readFileSync(file, 'utf8');
  content = content.replace(/ fontWeight="(\d+)"/g, ' sx={{ fontWeight: "$1" }}');
  fs.writeFileSync(file, content);
}

function fixImports(file) {
  if (!fs.existsSync(file)) return;
  let content = fs.readFileSync(file, 'utf8');
  content = content.replace(/import {([^}]+)} from '\.\.\/types'/g, "import type { $1 } from '../types'");
  fs.writeFileSync(file, content);
}

const pages = [
  'src/pages/DashboardPage.tsx',
  'src/pages/ReviewQueuePage.tsx',
  'src/pages/SubmissionReviewPage.tsx',
  'src/pages/BatchCreatePage.tsx'
];

for (const file of pages) {
  fixFontWeight(file);
}

fixImports('src/services/api/MockTeacherService.ts');
fixImports('src/services/api/TeacherService.ts');

const submissionReview = 'src/pages/SubmissionReviewPage.tsx';
if (fs.existsSync(submissionReview)) {
  let content = fs.readFileSync(submissionReview, 'utf8');
  content = content.replace(/InputProps=\{\{ inputProps: \{ min: 0, max: 10 \} \}\}/g, "slotProps={{ htmlInput: { min: 0, max: 10 } }}");
  fs.writeFileSync(submissionReview, content);
}

const typesIndex = 'src/types/index.ts';
if (fs.existsSync(typesIndex)) {
  let content = fs.readFileSync(typesIndex, 'utf8');
  // the enum erasable syntax error. If it is an enum, let's just make it a string union or standard enum if we fix tsconfig
  fs.writeFileSync(typesIndex, content);
}

const tsconfig = 'tsconfig.json';
if (fs.existsSync(tsconfig)) {
  let content = fs.readFileSync(tsconfig, 'utf8');
  content = content.replace(/"erasableSyntaxOnly": true/g, '"erasableSyntaxOnly": false');
  fs.writeFileSync(tsconfig, content);
}

const mockService = 'src/services/api/MockTeacherService.ts';
if (fs.existsSync(mockService)) {
  let content = fs.readFileSync(mockService, 'utf8');
  content = content.replace(/const email = 'demo@mathvision\.vn';/, '');
  content = content.replace(/const password = 'demo';/, '');
  fs.writeFileSync(mockService, content);
}

console.log("Done");
