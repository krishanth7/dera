declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
  interface Element {
    type: any;
    props: any;
    key: any;
  }
}

declare namespace React {
  interface ReactElement {
    type: any;
    props: any;
    key: any;
  }
  type ReactNode = any;
}

declare module "react" {
  export = React;
}
