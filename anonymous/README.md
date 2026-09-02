# Anonymous conference website

`index.html` in this directory is generated from the public page at the repository root.
Do not edit it directly. After changing the public page, regenerate and validate it with:

```sh
ruby scripts/build-anonymous.rb
```

To create a standalone directory for deployment, including all shared assets, run:

```sh
ruby scripts/build-anonymous.rb --package
```

Deploy `dist/anonymous-site` to a neutral host or account that does not identify the authors.
The page includes `noindex` directives, but an unguessable preview URL or host-level access
control is preferable during double-blind review. Do not deploy the repository itself, since
its URL, history, and public root page identify the authors.
