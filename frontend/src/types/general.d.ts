export type formState = {
  status?: string;
  errors?: {
    _form?: string[];
  };
};

export type responseApi<T> = {
  status: number;
  message: string;
  data: T;
};
