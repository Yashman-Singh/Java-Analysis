package com.example;

/**
 * Validates user data for correctness and completeness.
 */
public class UserValidator {

    /**
     * Validates a user's username.
     *
     * @param username the username to validate
     * @return true if the username is valid, false otherwise
     */
    public boolean validateUsername(String username) {
        return username != null && !username.trim().isEmpty();
    }

    /**
     * Validates a user's email.
     *
     * @param email the email to validate
     * @return true if the email is valid, false otherwise
     */
    public boolean validateEmail(String email) {
        return email != null && email.matches("^[A-Za-z0-9+_.-]+@(.+)$");
    }

    /**
     * Validates a user's age.
     *
     * @param age the age to validate
     * @return true if the age is valid, false otherwise
     */
    public boolean validateAge(int age) {
        return age >= 0 && age <= 150;
    }

    /**
     * Validates a user's data.
     *
     * @param user the user to validate
     * @return true if the user data is valid, false otherwise
     */
    public boolean validateUser(User user) {
        return validateUsername(user.getUsername()) &&
               validateEmail(user.getEmail()) &&
               validateAge(user.getAge());
    }
} 