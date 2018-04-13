module.exports = {
  map: { inline: false },
  plugins: [
    require('postcss-import')({ path: [__dirname, '__dirname/node_modules'] }),
    require('cssnano')({ preset: 'default' }),
  ]
}
