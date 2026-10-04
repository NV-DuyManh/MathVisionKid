import path from 'path';

it('does not let the Expo React Compiler read shared values during crop component render', () => {
  const babel = require('@babel/core');
  const traverse = require('@babel/traverse').default;
  const result = babel.transformFileSync(path.resolve(__dirname, '../../app/crop.tsx'), {
    babelrc: false, configFile: false, ast: true,
    presets: [require.resolve('babel-preset-expo')],
    caller: { name: 'metro', bundler: 'metro', platform: 'android', isDev: true, supportsReactCompiler: true },
  });
  const renderReads: string[] = [];
  const components: string[] = [];
  traverse(result.ast, {
    FunctionDeclaration(component: any) {
      const name = component.node.id?.name;
      if (!['StraightenRuler', 'CropEditor'].includes(name)) return;
      components.push(name);
      component.traverse({
        MemberExpression(member: any) {
          if (member.getFunctionParent() !== component) return;
          if (['value', 'get', 'set'].includes(member.node.property.name)) renderReads.push(`${name}: ${member.node.object.name}.${member.node.property.name}`);
        },
      });
    },
  });
  expect(components.sort()).toEqual(['CropEditor', 'StraightenRuler']);
  expect(renderReads).toEqual([]);
});
