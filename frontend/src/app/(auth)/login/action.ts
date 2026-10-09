"use server";

import { AuthFormState } from "@/types/auth";
import { LoginSchemaForm } from "@/validations/auth-validation";

export async function login(prevState: AuthFormState, formData: FormData) {
  const validatedFields = LoginSchemaForm.safeParse({
    email: formData.get("email") as string,
    password: formData.get("password") as string,
  });

  if (!validatedFields.success) {
    return {
      status: "error",
      errors: validatedFields.error.flatten().fieldErrors,
    };
  }
}
