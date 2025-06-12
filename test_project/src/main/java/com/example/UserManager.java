package com.example;

import java.util.List;
import java.util.stream.Collectors;

/**
 * Manages a collection of users and provides methods to add, remove, and find users.
 */
public class UserManager {
    private UserService userService;

    /**
     * Constructs a UserManager with a UserService.
     *
     * @param userService the service to manage users
     */
    public UserManager(UserService userService) {
        this.userService = userService;
    }

    /**
     * Adds a user to the collection.
     *
     * @param user the user to add
     */
    public void addUser(User user) {
        userService.addUser(user);
    }

    /**
     * Removes a user from the collection.
     *
     * @param user the user to remove
     */
    public void removeUser(User user) {
        userService.removeUser(user);
    }

    /**
     * Finds a user by their username.
     *
     * @param username the username to search for
     * @return the user if found, null otherwise
     */
    public User findUserByUsername(String username) {
        return userService.getUsers().stream()
                .filter(user -> user.getUsername().equals(username))
                .findFirst()
                .orElse(null);
    }

    /**
     * Returns a list of all users.
     *
     * @return a list of all users
     */
    public List<User> getAllUsers() {
        return userService.getUsers();
    }
} 